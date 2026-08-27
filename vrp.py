from pathlib import Path
import argparse
from typing import Dict, List, Optional, Tuple

from vrp_domain import Scenario, load_algorithm_config
from vrp_evaluator import SolutionEvaluation
from vrp_genetic import iter_genetic_algorithm, run_genetic_algorithm
from vrp_feasibility import assess_scenario
from vrp_reporting import build_solution_summary, save_solution_summary
from vrp_scenarios import SCENARIO_NAMES, load_benchmark_scenarios


ROOT = Path(__file__).parent
SCENARIO_PATH = ROOT / "data" / "hospital_scenario.json"
CONFIG_PATH = ROOT / "data" / "algorithm_config.json"
WIDTH, HEIGHT = 1100, 600
MAP_WIDTH = 800
NODE_RADIUS = 7


def run_once(
    scenario_path: str = str(SCENARIO_PATH),
    config_path: str = str(CONFIG_PATH),
    scenario_name: str = "base",
) -> Tuple[SolutionEvaluation, List[float]]:
    scenario = load_benchmark_scenarios(scenario_path)[scenario_name]
    config = load_algorithm_config(config_path)
    return run_genetic_algorithm(scenario, **config)


def _screen_locations(scenario: Scenario) -> Dict[str, Tuple[int, int]]:
    locations = [delivery.location for delivery in scenario.deliveries]
    locations.append(scenario.depot.location)
    max_x = max(location[0] for location in locations)
    max_y = max(location[1] for location in locations)
    scale = min((MAP_WIDTH - 40) / max_x, (HEIGHT - 40) / max_y)

    result = {
        delivery.id: (int(delivery.x * scale + 20), int(delivery.y * scale + 20))
        for delivery in scenario.deliveries
    }
    result["depot"] = (int(scenario.depot.x * scale + 20),
                       int(scenario.depot.y * scale + 20))
    return result


def _draw_text(screen, font, text: str, position: Tuple[int, int], color) -> None:
    screen.blit(font.render(text, True, color), position)


def _draw_solution(screen, scenario: Scenario, evaluation: SolutionEvaluation) -> None:
    import pygame

    locations = _screen_locations(scenario)
    screen.fill((248, 249, 246))
    pygame.draw.line(screen, (215, 218, 211), (MAP_WIDTH, 0), (MAP_WIDTH, HEIGHT), 2)

    for vehicle in scenario.vehicles:
        route = evaluation.routes[vehicle.id]
        points = [locations["depot"]]
        points.extend(locations[delivery_id] for delivery_id in route)
        points.append(locations["depot"])
        pygame.draw.lines(screen, vehicle.color, False, points, 3)
        metrics = evaluation.route_metrics[vehicle.id]
        if not metrics.is_valid:
            for point in points[1:-1]:
                pygame.draw.circle(screen, (205, 35, 35), point, NODE_RADIUS + 5, 2)

    priority_colors = {
        "critical": (190, 35, 35),
        "high": (220, 125, 25),
        "normal": (45, 90, 170),
        "low": (110, 110, 110),
    }
    for delivery in scenario.deliveries:
        location = locations[delivery.id]
        pygame.draw.circle(screen, priority_colors[delivery.priority], location, NODE_RADIUS)
        pygame.draw.circle(screen, (35, 35, 35), location, NODE_RADIUS, 1)

    for vehicle in scenario.vehicles:
        for sequence, delivery_id in enumerate(evaluation.routes[vehicle.id], start=1):
            location = locations[delivery_id]
            _draw_text(screen, pygame.font.SysFont("DejaVu Sans", 11, bold=True),
                       str(sequence), (location[0] - 4, location[1] - 7), (255, 255, 255))

    pygame.draw.circle(screen, (25, 25, 25), locations["depot"], NODE_RADIUS + 3)


def _draw_history(screen, history: List[float]) -> None:
    import pygame

    if len(history) < 2:
        return
    left, top, width, height = MAP_WIDTH + 25, 470, WIDTH - MAP_WIDTH - 45, 95
    minimum, maximum = min(history), max(history)
    spread = maximum - minimum or 1
    points = [
        (int(left + index * width / (len(history) - 1)),
         int(top + height - (value - minimum) * height / spread))
        for index, value in enumerate(history)
    ]
    pygame.draw.rect(screen, (225, 227, 222), (left, top, width, height), 1)
    pygame.draw.lines(screen, (30, 100, 170), False, points, 2)


def _draw_panel(
    screen, scenario: Scenario, evaluation: SolutionEvaluation,
    generation_number: int, history: List[float],
) -> None:
    import pygame

    font = pygame.font.SysFont("DejaVu Sans", 16)
    bold_font = pygame.font.SysFont("DejaVu Sans", 19, bold=True)
    x = MAP_WIDTH + 25
    _draw_text(screen, bold_font, "VRP hospitalar", (x, 25), (25, 25, 25))
    _draw_text(screen, font, f"Geracao: {generation_number}", (x, 45), (25, 25, 25))
    _draw_text(screen, font, f"Fitness: {evaluation.fitness:.2f}", (x, 65), (25, 25, 25))
    _draw_text(screen, font, f"Distancia: {evaluation.total_distance:.2f}", (x, 90), (25, 25, 25))
    _draw_text(screen, font, f"Valida: {'sim' if evaluation.is_valid else 'nao'}", (x, 115), (25, 25, 25))

    for index, vehicle in enumerate(scenario.vehicles):
        metrics = evaluation.route_metrics[vehicle.id]
        y = 170 + index * 85
        pygame.draw.rect(screen, vehicle.color, (x, y + 4, 12, 12))
        _draw_text(screen, bold_font, vehicle.id, (x + 22, y), (25, 25, 25))
        _draw_text(screen, font, f"Distancia: {metrics.distance:.1f}", (x, y + 28), (55, 55, 55))
        _draw_text(screen, font, f"Carga: {metrics.load:.1f}/{vehicle.capacity:.1f}", (x, y + 50), (55, 55, 55))
        _draw_text(screen, font, f"Autonomia: {metrics.distance:.1f}/{vehicle.autonomy:.1f}", (x, y + 72), (55, 55, 55))
        if not metrics.is_valid:
            _draw_text(screen, font, "VIOLACAO", (x + 125, y), (190, 35, 35))

    _draw_text(screen, font, "Fitness por geracao", (x, 445), (55, 55, 55))
    _draw_history(screen, history)


def main(max_generations: Optional[int] = None, scenario_name: str = "base") -> None:
    import pygame

    scenario = load_benchmark_scenarios(str(SCENARIO_PATH))[scenario_name]
    config = load_algorithm_config(str(CONFIG_PATH))
    feasibility = assess_scenario(scenario)
    if not feasibility.is_feasible:
        print("Aviso: o cenário possui restrições potencialmente inviáveis:")
        for issue in feasibility.issues:
            print(f"- {issue}")
    config["max_generations"] = max_generations
    if max_generations is None:
        config["stagnation_limit"] = None
    pygame.init()

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("VRP hospitalar usando algoritmo genetico")

    clock = pygame.time.Clock()
    generations = iter_genetic_algorithm(scenario, **config)
    evaluation = None
    history = []
    generation_number = 0
    finished = False
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                running = False

        if running and not finished:
            try:
                generation_number, evaluation, history = next(generations)
                print(f"Generation {generation_number}: Best fitness = {evaluation.fitness:.2f}")
            except StopIteration:
                finished = True

        if evaluation is not None:
            _draw_solution(screen, scenario, evaluation)
            _draw_panel(screen, scenario, evaluation, generation_number, history)
        pygame.display.flip()
        clock.tick(30)

    if evaluation is not None:
        print(f"Fitness final: {evaluation.fitness:.2f}")
        print(f"Distancia total: {evaluation.total_distance:.2f}")
        print(f"Solucao valida: {evaluation.is_valid}")
        print(f"Geracoes executadas: {len(history)}")
        for vehicle_id, route in evaluation.routes.items():
            print(f"{vehicle_id}: {' -> '.join(route)}")
            summary = build_solution_summary(
                scenario, evaluation, scenario_name, history
            )
            report_path = ROOT / "results" / f"vrp_report_{scenario_name}.json"
            save_solution_summary(summary, str(report_path))
            print(
                f"Resumo estruturado preparado: {summary['deliveries']['total']} entregas, "
                f"{summary['evolution']['generations']} geracoes"
            )
            print(f"Report salvo em: {report_path}")

    pygame.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Executa o VRP hospitalar otimizado")
    parser.add_argument(
        "--generations",
        type=int,
        default=None,
        help="Limite de geracoes; sem valor, executa ate Q",
    )
    parser.add_argument(
        "--scenario",
        choices=SCENARIO_NAMES,
        default="base",
        help="Cenario hospitalar para visualizar",
    )
    arguments = parser.parse_args()
    main(arguments.generations, arguments.scenario)
