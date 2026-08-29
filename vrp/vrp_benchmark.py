from dataclasses import dataclass, replace
import argparse
import csv
from pathlib import Path
import random
import statistics
import time
from typing import Dict, List, Optional, Sequence

from vrp.vrp_domain import Scenario, load_algorithm_config, load_scenario
from vrp.vrp_evaluator import SolutionEvaluation, calculate_distance, evaluate_solution
from vrp.vrp_genetic import run_genetic_algorithm, split_solution
from vrp.vrp_repair import repair_routes
from vrp.vrp_scenarios import load_benchmark_scenarios


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = Path("results")


@dataclass(frozen=True)
class BenchmarkResult:
    scenario: str
    method: str
    evaluation: SolutionEvaluation
    elapsed_seconds: float
    random_seed: int
    history: List[float]
    repetition: int = 1


CSV_FIELDS = [
    "method",
    "scenario",
    "repetition",
    "random_seed",
    "max_generations",
    "population_size",
    "fitness",
    "total_distance",
    "penalty",
    "valid",
    "elapsed_seconds",
    "generations_executed",
]

SUMMARY_FIELDS = [
    "scenario",
    "method",
    "runs",
    "valid_runs",
    "valid_rate",
    "mean_fitness",
    "median_fitness",
    "best_fitness",
    "worst_fitness",
    "fitness_stdev",
    "mean_distance",
    "mean_penalty",
    "mean_elapsed_seconds",
    "mean_generations_executed",
]

EVOLUTION_FIELDS = ["scenario", "method", "repetition", "generation", "best_fitness"]


def _evaluate_order(
    scenario: Scenario,
    delivery_ids: List[str],
    config: Dict[str, float],
) -> SolutionEvaluation:
    vehicle_ids = [vehicle.id for vehicle in scenario.vehicles]
    routes = split_solution(delivery_ids, vehicle_ids)
    return evaluate_solution(
        scenario,
        repair_routes(scenario, routes),
        config["capacity_penalty"],
        config["autonomy_penalty"],
        config["priority_penalty"],
        config.get("critical_penalty", 100000),
        config.get("critical_position_limit", 1),
    )


def random_solution(
    scenario: Scenario, config: Dict[str, float], samples: int = 100
) -> SolutionEvaluation:
    rng = random.Random(int(config["random_seed"]))
    delivery_ids = [delivery.id for delivery in scenario.deliveries]
    candidates = [rng.sample(delivery_ids, len(delivery_ids)) for _ in range(samples)]
    return min((_evaluate_order(scenario, candidate, config) for candidate in candidates),
               key=lambda evaluation: evaluation.fitness)


def nearest_neighbor_solution(
    scenario: Scenario, config: Dict[str, float]
) -> SolutionEvaluation:
    remaining = {delivery.id: delivery for delivery in scenario.deliveries}
    routes = {vehicle.id: [] for vehicle in scenario.vehicles}

    critical_deliveries = [
        delivery for delivery in scenario.deliveries
        if delivery.priority == "critical"
    ]
    for vehicle, delivery in zip(scenario.vehicles, critical_deliveries):
        routes[vehicle.id].append(delivery.id)
        del remaining[delivery.id]

    while remaining:
        candidates = []
        for vehicle in scenario.vehicles:
            route = routes[vehicle.id]
            current_location = scenario.depot.location
            if route:
                current_location = next(
                    delivery.location for delivery in scenario.deliveries
                    if delivery.id == route[-1]
                )
            load = sum(
                next(delivery.demand for delivery in scenario.deliveries
                     if delivery.id == delivery_id)
                for delivery_id in route
            )
            for delivery in remaining.values():
                if load + delivery.demand <= vehicle.capacity:
                    candidates.append((
                        calculate_distance(current_location, delivery.location),
                        vehicle.id,
                        delivery.id,
                    ))

        if not candidates:
            vehicle_id = min(routes, key=lambda key: len(routes[key]))
            delivery_id = next(iter(remaining))
        else:
            _, vehicle_id, delivery_id = min(candidates)
        routes[vehicle_id].append(delivery_id)
        del remaining[delivery_id]

    return evaluate_solution(
        scenario,
        repair_routes(scenario, routes),
        config["capacity_penalty"],
        config["autonomy_penalty"],
        config["priority_penalty"],
        config.get("critical_penalty", 100000),
        config.get("critical_position_limit", 1),
    )


def run_benchmark(
    scenario: Scenario, config: Dict[str, float], scenario_name: str = "base",
    selected_methods: Optional[Sequence[str]] = None,
) -> List[BenchmarkResult]:
    results = []
    all_methods = [
        ("random", lambda: random_solution(scenario, config)),
        ("nearest_neighbor", lambda: nearest_neighbor_solution(scenario, config)),
        ("genetic", lambda: run_genetic_algorithm(scenario, **config)),
    ]
    methods = [
        item for item in all_methods
        if selected_methods is None or item[0] in selected_methods
    ]
    for method, function in methods:
        print(
            f"[benchmark] iniciando | cenario={scenario_name} | metodo={method}",
            flush=True,
        )
        started_at = time.perf_counter()
        result = function()
        if method == "genetic":
            evaluation, history = result
        else:
            evaluation, history = result, [result.fitness]
        benchmark_result = BenchmarkResult(
            scenario_name,
            method,
            evaluation,
            time.perf_counter() - started_at,
            int(config["random_seed"]),
            history,
        )
        results.append(benchmark_result)
        print(
            f"[benchmark] concluido | cenario={scenario_name} | metodo={method} | "
            f"geracoes={len(history)} | fitness={evaluation.fitness:.2f} | "
            f"valida={evaluation.is_valid} | tempo={benchmark_result.elapsed_seconds:.2f}s",
            flush=True,
        )
    return results


def run_benchmark_repetitions(
    scenario: Scenario, config: Dict[str, float], repetitions: int = 5,
    scenario_name: str = "base",
) -> List[BenchmarkResult]:
    if repetitions < 1:
        raise ValueError("Repetitions must be positive")

    results = []
    baseline_config = dict(config)
    baseline_config["random_seed"] = int(config["random_seed"])
    results.extend(
        replace(result, repetition=1)
        for result in run_benchmark(
            scenario, baseline_config, scenario_name, ("nearest_neighbor",)
        )
    )
    for repetition in range(1, repetitions + 1):
        repetition_config = dict(config)
        repetition_config["random_seed"] = int(config["random_seed"]) + repetition - 1
        results.extend(
            replace(result, repetition=repetition)
            for result in run_benchmark(
                scenario, repetition_config, scenario_name, ("random", "genetic")
            )
        )
    return results


def write_benchmark_csv(
    results: List[BenchmarkResult], config: Dict[str, float], path: str
) -> None:
    rows = [
        {
            "method": result.method,
            "scenario": result.scenario,
            "repetition": result.repetition,
            "random_seed": result.random_seed,
            "max_generations": config["max_generations"],
            "population_size": config["population_size"],
            "fitness": f"{result.evaluation.fitness:.6f}",
            "total_distance": f"{result.evaluation.total_distance:.6f}",
            "penalty": f"{result.evaluation.penalty:.6f}",
            "valid": result.evaluation.is_valid,
            "elapsed_seconds": f"{result.elapsed_seconds:.6f}",
            "generations_executed": len(result.history),
        }
        for result in results
    ]
    output_path = Path(path)
    with output_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_benchmark_summary_csv(results: List[BenchmarkResult], path: str) -> None:
    grouped = {}
    for result in results:
        grouped.setdefault((result.scenario, result.method), []).append(result)

    rows = []
    for (scenario, method), method_results in sorted(grouped.items()):
        fitness_values = [result.evaluation.fitness for result in method_results]
        distance_values = [result.evaluation.total_distance for result in method_results]
        penalty_values = [result.evaluation.penalty for result in method_results]
        elapsed_values = [result.elapsed_seconds for result in method_results]
        generation_values = [len(result.history) for result in method_results]
        valid_runs = sum(result.evaluation.is_valid for result in method_results)
        rows.append({
            "scenario": scenario,
            "method": method,
            "runs": len(method_results),
            "valid_runs": valid_runs,
            "valid_rate": f"{valid_runs / len(method_results):.6f}",
            "mean_fitness": f"{statistics.mean(fitness_values):.6f}",
            "median_fitness": f"{statistics.median(fitness_values):.6f}",
            "best_fitness": f"{min(fitness_values):.6f}",
            "worst_fitness": f"{max(fitness_values):.6f}",
            "fitness_stdev": f"{statistics.stdev(fitness_values):.6f}" if len(fitness_values) > 1 else "0.000000",
            "mean_distance": f"{statistics.mean(distance_values):.6f}",
            "mean_penalty": f"{statistics.mean(penalty_values):.6f}",
            "mean_elapsed_seconds": f"{statistics.mean(elapsed_values):.6f}",
            "mean_generations_executed": f"{statistics.mean(generation_values):.6f}",
        })

    output_path = Path(path)
    with output_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_benchmark_evolution_csv(results: List[BenchmarkResult], path: str) -> None:
    rows = []
    for result in results:
        rows.extend(
            {
                "scenario": result.scenario,
                "method": result.method,
                "repetition": result.repetition,
                "generation": generation,
                "best_fitness": f"{fitness:.6f}",
            }
            for generation, fitness in enumerate(result.history, start=1)
        )
    with Path(path).open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=EVOLUTION_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compara metodos de roteamento VRP")
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument("--generations", type=int, default=None)
    parser.add_argument("--output", default="benchmark_results.csv")
    parser.add_argument("--scenarios", nargs="+", default=["base"])
    arguments = parser.parse_args()

    scenarios = load_benchmark_scenarios(str(PROJECT_ROOT / "data" / "hospital_scenario.json"))
    config = load_algorithm_config(str(PROJECT_ROOT / "data" / "algorithm_config.json"))
    if arguments.generations is not None:
        config["max_generations"] = arguments.generations
    unknown = set(arguments.scenarios) - set(scenarios)
    if unknown:
        parser.error(f"Cenarios desconhecidos: {', '.join(sorted(unknown))}")
    results = []
    total_scenarios = len(arguments.scenarios)
    for scenario_index, scenario_name in enumerate(arguments.scenarios, start=1):
        print(
            f"[benchmark] cenario {scenario_index}/{total_scenarios}: {scenario_name} | "
            f"repeticoes={arguments.repetitions} | geracoes_max={config['max_generations']}",
            flush=True,
        )
        results.extend(run_benchmark_repetitions(
            scenarios[scenario_name], config, arguments.repetitions, scenario_name
        ))
    output_path = Path(arguments.output)
    if output_path.parent == Path("."):
        output_path = RESULTS_DIR / output_path.name
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_benchmark_csv(results, config, str(output_path))
    summary_path = output_path.with_name(
        f"{output_path.stem}_summary.csv"
    )
    write_benchmark_summary_csv(results, summary_path)
    evolution_path = output_path.with_name(
        f"{output_path.stem}_evolution.csv"
    )
    write_benchmark_evolution_csv(results, evolution_path)
    print(
        f"[benchmark] finalizado | resultados={output_path} | "
        f"resumo={summary_path} | evolucao={evolution_path}",
        flush=True,
    )
    for result in results:
        print(
            f"{result.method}: fitness={result.evaluation.fitness:.2f}, "
            f"distance={result.evaluation.total_distance:.2f}, "
            f"valid={result.evaluation.is_valid}, "
            f"time={result.elapsed_seconds:.4f}s"
        )


if __name__ == "__main__":
    main()