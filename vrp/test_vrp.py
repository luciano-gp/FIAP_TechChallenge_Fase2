import unittest
from pathlib import Path

from vrp.vrp_domain import load_scenario
from vrp.vrp_benchmark import (
    nearest_neighbor_solution,
    run_benchmark,
    write_benchmark_summary_csv,
)
from vrp.vrp_evaluator import evaluate_solution
from vrp.vrp_genetic import run_genetic_algorithm
from vrp.vrp_genetic import mutate_between_vehicles, split_variable_solution
from vrp.vrp_repair import repair_routes
from vrp.vrp_scenarios import SCENARIO_NAMES, load_benchmark_scenarios
from vrp.vrp_feasibility import assess_scenario
from vrp.vrp_reporting import build_solution_summary, save_solution_summary
from vrp import run_once


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROOT = PROJECT_ROOT
SCENARIO_PATH = PROJECT_ROOT / "data" / "hospital_scenario.json"


class VrpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scenario = load_scenario(str(SCENARIO_PATH))

    def test_scenario_has_expected_structure(self):
        self.assertEqual(len(self.scenario.deliveries), 20)
        self.assertEqual(len(self.scenario.vehicles), 3)
        self.assertEqual(
            {delivery.priority for delivery in self.scenario.deliveries},
            {"critical", "high", "normal", "low"},
        )

    def test_complete_solution_has_no_missing_or_duplicate_deliveries(self):
        delivery_ids = [delivery.id for delivery in self.scenario.deliveries]
        routes = {
            "V01": delivery_ids[:7],
            "V02": delivery_ids[7:14],
            "V03": delivery_ids[14:],
        }
        evaluation = evaluate_solution(self.scenario, routes)
        self.assertEqual(evaluation.missing_delivery_ids, ())
        self.assertEqual(evaluation.duplicate_delivery_ids, ())
        self.assertGreater(evaluation.total_distance, 0)

    def test_capacity_violation_is_penalized(self):
        delivery_ids = [delivery.id for delivery in self.scenario.deliveries]
        evaluation = evaluate_solution(
            self.scenario,
            {"V01": delivery_ids, "V02": [], "V03": []},
        )
        self.assertGreater(evaluation.route_metrics["V01"].capacity_excess, 0)
        self.assertGreater(evaluation.penalty, 0)
        self.assertFalse(evaluation.is_valid)

    def test_critical_delivery_must_be_first_in_route(self):
        delivery_ids = [delivery.id for delivery in self.scenario.deliveries]
        remaining_ids = [delivery_id for delivery_id in delivery_ids
                         if delivery_id not in {"D01", "D07", "D15"}]
        valid_routes = {
            "V01": ["D01"] + remaining_ids[:6],
            "V02": ["D07"] + remaining_ids[6:12],
            "V03": ["D15"] + remaining_ids[12:],
        }
        invalid_routes = dict(valid_routes)
        invalid_routes["V01"] = [valid_routes["V01"][1], "D01"] + valid_routes["V01"][2:]

        valid_evaluation = evaluate_solution(self.scenario, valid_routes)
        invalid_evaluation = evaluate_solution(self.scenario, invalid_routes)
        self.assertEqual(
            valid_evaluation.route_metrics["V01"].critical_priority_violations,
            0,
        )
        self.assertEqual(
            invalid_evaluation.route_metrics["V01"].critical_priority_violations,
            1,
        )
        self.assertFalse(invalid_evaluation.is_valid)
        self.assertGreater(
            invalid_evaluation.route_metrics["V01"].critical_priority_violations,
            valid_evaluation.route_metrics["V01"].critical_priority_violations,
        )

    def test_algorithm_is_reproducible(self):
        arguments = {
            "population_size": 20,
            "max_generations": 10,
            "stagnation_limit": 10,
            "random_seed": 42,
        }
        first, first_history = run_genetic_algorithm(self.scenario, **arguments)
        second, second_history = run_genetic_algorithm(self.scenario, **arguments)
        self.assertEqual(first.routes, second.routes)
        self.assertEqual(first_history, second_history)
        self.assertEqual(
            sorted(delivery_id for route in first.routes.values() for delivery_id in route),
            sorted(delivery.id for delivery in self.scenario.deliveries),
        )

    def test_benchmark_evaluates_all_methods(self):
        config = {
            "population_size": 10,
            "max_generations": 3,
            "stagnation_limit": 3,
            "mutation_probability": 0.25,
            "crossover_probability": 0.9,
            "random_seed": 42,
            "capacity_penalty": 10000,
            "autonomy_penalty": 10000,
            "priority_penalty": 100,
        }
        results = run_benchmark(self.scenario, config)
        self.assertEqual(
            [result.method for result in results],
            ["random", "nearest_neighbor", "genetic"],
        )

    def test_nearest_neighbor_respects_critical_priority(self):
        config = {
            "capacity_penalty": 10000,
            "autonomy_penalty": 10000,
            "priority_penalty": 100,
            "critical_penalty": 100000,
            "critical_position_limit": 1,
        }
        evaluation = nearest_neighbor_solution(self.scenario, config)
        self.assertTrue(evaluation.is_valid)
        self.assertTrue(all(
            metrics.critical_priority_violations == 0
            for metrics in evaluation.route_metrics.values()
        ))

    def test_vehicle_mutation_preserves_delivery_permutation(self):
        import random

        delivery_ids = [delivery.id for delivery in self.scenario.deliveries]
        mutated = mutate_between_vehicles(
            delivery_ids, vehicle_count=3, probability=1, rng=random.Random(42)
        )
        self.assertEqual(sorted(mutated), sorted(delivery_ids))

    def test_variable_breakpoints_create_uneven_routes(self):
        delivery_ids = [delivery.id for delivery in self.scenario.deliveries]
        routes = split_variable_solution(delivery_ids, [2, 15], ["V01", "V02", "V03"])
        self.assertEqual([len(routes[vehicle_id]) for vehicle_id in ("V01", "V02", "V03")], [2, 13, 5])

    def test_repair_removes_duplicates_and_prioritizes_critical_deliveries(self):
        routes = {
            "V01": ["D02", "D01", "D03", "D01"],
            "V02": ["D04", "D07"],
            "V03": ["D15"],
        }
        repaired = repair_routes(self.scenario, routes)
        evaluation = evaluate_solution(self.scenario, repaired)
        self.assertEqual(evaluation.duplicate_delivery_ids, ())
        self.assertEqual(evaluation.missing_delivery_ids, ())
        self.assertEqual(repaired["V01"][0], "D01")
        self.assertEqual(repaired["V02"][0], "D07")
        self.assertEqual(repaired["V03"][0], "D15")

    def test_benchmark_summary_contains_one_row_per_method(self):
        import csv
        from tempfile import TemporaryDirectory

        config = {
            "population_size": 10,
            "max_generations": 3,
            "stagnation_limit": 3,
            "mutation_probability": 0.25,
            "crossover_probability": 0.9,
            "random_seed": 42,
            "capacity_penalty": 10000,
            "autonomy_penalty": 10000,
            "priority_penalty": 100,
        }
        results = run_benchmark(self.scenario, config)
        with TemporaryDirectory() as directory:
            path = Path(directory) / "summary.csv"
            write_benchmark_summary_csv(results, str(path))
            with path.open(encoding="utf-8") as summary_file:
                rows = list(csv.DictReader(summary_file))
        self.assertEqual(
            {row["method"] for row in rows},
            {"random", "nearest_neighbor", "genetic"},
        )

    def test_benchmark_scenarios_have_expected_variations(self):
        scenarios = load_benchmark_scenarios(str(SCENARIO_PATH))
        self.assertEqual(
            set(scenarios),
            set(SCENARIO_NAMES),
        )
        self.assertEqual(len(scenarios["maior"].deliveries), 40)
        self.assertEqual(len(scenarios["frota_reduzida"].vehicles), 2)
        self.assertFalse(assess_scenario(scenarios["capacidade_insuficiente"]).is_feasible)

    def test_benchmark_result_path_uses_results_directory(self):
        from vrp.vrp_benchmark import RESULTS_DIR

        self.assertEqual(str(RESULTS_DIR), "results")

    def test_visualization_entrypoint_accepts_named_scenario(self):
        evaluation, history = run_once(
            config_path=str(ROOT / "data" / "algorithm_config.json"),
            scenario_name="alta_demanda",
        )
        self.assertTrue(evaluation.routes)
        self.assertGreater(len(history), 0)

    def test_base_scenario_is_feasible(self):
        report = assess_scenario(self.scenario)
        self.assertTrue(report.is_feasible)

    def test_valid_solution_stability_can_stop_algorithm_early(self):
        result, history = run_genetic_algorithm(
            self.scenario,
            population_size=10,
            max_generations=100,
            stagnation_limit=None,
            valid_stability_limit=2,
            random_seed=42,
        )
        self.assertTrue(result.is_valid)
        self.assertLess(len(history), 100)

    def test_solution_summary_is_json_serializable(self):
        import json

        evaluation, history = run_genetic_algorithm(
            self.scenario,
            population_size=10,
            max_generations=3,
            stagnation_limit=None,
            random_seed=42,
        )
        summary = build_solution_summary(
            self.scenario, evaluation, "base", history,
            comparison=[
                {"method": "nearest_neighbor", "fitness": evaluation.fitness + 1000},
            ],
            average_speed=40,
        )
        serialized = json.dumps(summary)
        self.assertIn('"objective"', serialized)
        self.assertEqual(summary["deliveries"]["total"], 20)
        self.assertEqual(len(summary["deliveries"]["details"]), 20)
        self.assertEqual(len(summary["vehicles"][0]["route_legs"]), summary["vehicles"][0]["stops"] + 1)
        self.assertIn("performance", summary)
        self.assertIn("transport", summary)
        self.assertGreater(summary["transport"]["estimated_total_time"], 0)
        self.assertIn("constraints", summary)
        self.assertIn("analysis", summary)
        self.assertEqual(len(summary["vehicles"][0]["route_details"]), summary["vehicles"][0]["stops"])
        self.assertIn("capacity_utilization", summary["vehicles"][0])
        self.assertTrue(summary["analysis"]["recommendations"])
        self.assertEqual(len(summary["vehicles"]), 3)
        self.assertEqual(summary["evolution"]["generations"], 3)

    def test_solution_summary_can_be_saved_as_json(self):
        import json
        from tempfile import TemporaryDirectory

        evaluation, history = run_genetic_algorithm(
            self.scenario,
            population_size=10,
            max_generations=2,
            stagnation_limit=None,
            random_seed=42,
        )
        summary = build_solution_summary(self.scenario, evaluation, "base", history)
        with TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            save_solution_summary(summary, str(path))
            saved = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(saved["scenario"], "base")
        self.assertEqual(saved["deliveries"]["total"], 20)

    def test_feasibility_detects_insufficient_total_capacity(self):
        scenario = load_benchmark_scenarios()["base"]
        vehicles = tuple(
            vehicle.__class__(vehicle.id, 1, vehicle.autonomy, vehicle.color)
            for vehicle in scenario.vehicles
        )
        report = assess_scenario(scenario.__class__(scenario.depot, scenario.deliveries, list(vehicles)))
        self.assertIn("A demanda total excede a capacidade total da frota", report.issues)


if __name__ == "__main__":
    unittest.main()
