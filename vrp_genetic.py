import random
from itertools import count
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from vrp_domain import Scenario
from vrp_evaluator import SolutionEvaluation, evaluate_solution
from vrp_repair import repair_routes


RoutePlan = Tuple[List[str], List[int]]


def split_solution(delivery_ids: Sequence[str], vehicle_ids: Sequence[str]) -> Dict[str, List[str]]:
    if not vehicle_ids:
        raise ValueError("At least one vehicle is required")

    routes = {vehicle_id: [] for vehicle_id in vehicle_ids}
    base_size, remainder = divmod(len(delivery_ids), len(vehicle_ids))
    start = 0
    for index, vehicle_id in enumerate(vehicle_ids):
        route_size = base_size + (1 if index < remainder else 0)
        routes[vehicle_id] = list(delivery_ids[start:start + route_size])
        start += route_size
    return routes


def split_variable_solution(
    delivery_ids: Sequence[str], breakpoints: Sequence[int], vehicle_ids: Sequence[str]
) -> Dict[str, List[str]]:
    if not vehicle_ids:
        raise ValueError("At least one vehicle is required")

    valid_breakpoints = sorted({
        breakpoint for breakpoint in breakpoints
        if 0 < breakpoint < len(delivery_ids)
    })
    cut_points = [0] + valid_breakpoints[:len(vehicle_ids) - 1] + [len(delivery_ids)]
    routes = {vehicle_id: [] for vehicle_id in vehicle_ids}
    for index, vehicle_id in enumerate(vehicle_ids):
        routes[vehicle_id] = list(delivery_ids[cut_points[index]:cut_points[index + 1]])
    return routes


def generate_population(
    delivery_ids: Sequence[str], population_size: int, rng: random.Random
) -> List[List[str]]:
    return [rng.sample(list(delivery_ids), len(delivery_ids))
            for _ in range(population_size)]


def generate_route_population(
    delivery_ids: Sequence[str], vehicle_count: int, population_size: int, rng: random.Random
) -> List[RoutePlan]:
    if vehicle_count < 1:
        raise ValueError("At least one vehicle is required")
    if len(delivery_ids) < vehicle_count - 1:
        raise ValueError("There are not enough deliveries for the vehicle cuts")
    available_cuts = list(range(1, len(delivery_ids)))
    return [
        (rng.sample(list(delivery_ids), len(delivery_ids)),
         sorted(rng.sample(available_cuts, min(vehicle_count - 1, len(available_cuts)))))
        for _ in range(population_size)
    ]


def order_crossover(
    parent1: Sequence[str], parent2: Sequence[str], rng: random.Random
) -> List[str]:
    if len(parent1) != len(parent2):
        raise ValueError("Parents must have the same length")
    if len(parent1) < 2:
        return list(parent1)

    start, end = sorted(rng.sample(range(len(parent1)), 2))
    child: List[str] = [""] * len(parent1)
    child[start:end + 1] = parent1[start:end + 1]
    remaining = [gene for gene in parent2 if gene not in child]
    remaining_index = 0
    for index in range(len(child)):
        if not child[index]:
            child[index] = remaining[remaining_index]
            remaining_index += 1
    return child


def mutate(solution: Sequence[str], probability: float, rng: random.Random) -> List[str]:
    mutated = list(solution)
    if len(mutated) >= 2 and rng.random() < probability:
        start, end = sorted(rng.sample(range(len(mutated)), 2))
        mutated[start:end + 1] = reversed(mutated[start:end + 1])
    return mutated


def mutate_between_vehicles(
    solution: Sequence[str], vehicle_count: int, probability: float, rng: random.Random,
    breakpoints: Optional[Sequence[int]] = None,
) -> List[str]:
    mutated = list(solution)
    if vehicle_count < 2 or len(mutated) < vehicle_count or rng.random() >= probability:
        return mutated

    cuts = sorted({
        breakpoint for breakpoint in (breakpoints or [])
        if 0 < breakpoint < len(mutated)
    })
    if breakpoints is None:
        base_size, remainder = divmod(len(mutated), vehicle_count)
        cuts = []
        position = 0
        for vehicle_index in range(vehicle_count - 1):
            position += base_size + (1 if vehicle_index < remainder else 0)
            cuts.append(position)
    cut_points = [0] + cuts[:vehicle_count - 1] + [len(mutated)]
    boundaries = [
        range(cut_points[index], cut_points[index + 1])
        for index in range(len(cut_points) - 1)
    ]

    first_vehicle, second_vehicle = rng.sample(range(vehicle_count), 2)
    first_index = rng.choice(list(boundaries[first_vehicle]))
    second_index = rng.choice(list(boundaries[second_vehicle]))
    mutated[first_index], mutated[second_index] = mutated[second_index], mutated[first_index]
    return mutated


def mutate_route_plan(
    plan: RoutePlan, vehicle_count: int, probability: float, rng: random.Random
) -> RoutePlan:
    delivery_ids, breakpoints = plan
    mutated_ids = mutate(delivery_ids, probability, rng)
    mutated_breakpoints = list(breakpoints)
    if vehicle_count > 1 and mutated_breakpoints and rng.random() < probability:
        index = rng.randrange(len(mutated_breakpoints))
        direction = rng.choice((-1, 1))
        mutated_breakpoints[index] += direction
        mutated_breakpoints = sorted(set(
            breakpoint for breakpoint in mutated_breakpoints
            if 0 < breakpoint < len(mutated_ids)
        ))
        while len(mutated_breakpoints) < vehicle_count - 1:
            candidates = [
                point for point in range(1, len(mutated_ids))
                if point not in mutated_breakpoints
            ]
            if not candidates:
                break
            mutated_breakpoints.append(rng.choice(candidates))
            mutated_breakpoints.sort()
    return mutated_ids, mutated_breakpoints


def _tournament(
    population: Sequence[RoutePlan], evaluations: Sequence[SolutionEvaluation], rng: random.Random
) -> RoutePlan:
    candidates = [rng.randrange(len(population)) for _ in range(min(3, len(population)))]
    winner = min(candidates, key=lambda index: evaluations[index].fitness)
    return population[winner]


def run_genetic_algorithm(
    scenario: Scenario,
    population_size: int = 100,
    max_generations: Optional[int] = 500,
    mutation_probability: float = 0.25,
    crossover_probability: float = 0.9,
    stagnation_limit: Optional[int] = 75,
    random_seed: int = 42,
    capacity_penalty: float = 10000,
    autonomy_penalty: float = 10000,
    priority_penalty: float = 100,
    critical_penalty: float = 100000,
    critical_position_limit: int = 1,
    vehicle_swap_probability: float = 0.2,
    valid_stability_limit: Optional[int] = None,
    stop_requested: Optional[Callable[[], bool]] = None,
) -> Tuple[SolutionEvaluation, List[float]]:
    if population_size < 2:
        raise ValueError("Population size must be at least 2")
    if max_generations is not None and max_generations < 1:
        raise ValueError("Maximum generations must be positive")

    results = iter_genetic_algorithm(
        scenario,
        population_size=population_size,
        max_generations=max_generations,
        mutation_probability=mutation_probability,
        crossover_probability=crossover_probability,
        stagnation_limit=stagnation_limit,
        random_seed=random_seed,
        capacity_penalty=capacity_penalty,
        autonomy_penalty=autonomy_penalty,
        priority_penalty=priority_penalty,
        critical_penalty=critical_penalty,
        critical_position_limit=critical_position_limit,
        vehicle_swap_probability=vehicle_swap_probability,
        valid_stability_limit=valid_stability_limit,
        stop_requested=stop_requested,
    )
    last_result = None
    for last_result in results:
        pass
    if last_result is None:
        raise RuntimeError("The algorithm stopped before evaluating a generation")
    return last_result[1], last_result[2]


def iter_genetic_algorithm(
    scenario: Scenario,
    population_size: int = 100,
    max_generations: Optional[int] = 500,
    mutation_probability: float = 0.25,
    crossover_probability: float = 0.9,
    stagnation_limit: Optional[int] = 75,
    random_seed: int = 42,
    capacity_penalty: float = 10000,
    autonomy_penalty: float = 10000,
    priority_penalty: float = 100,
    critical_penalty: float = 100000,
    critical_position_limit: int = 1,
    vehicle_swap_probability: float = 0.2,
    valid_stability_limit: Optional[int] = None,
    stop_requested: Optional[Callable[[], bool]] = None,
):
    if population_size < 2:
        raise ValueError("Population size must be at least 2")
    if max_generations is not None and max_generations < 1:
        raise ValueError("Maximum generations must be positive")

    rng = random.Random(random_seed)
    delivery_ids = [delivery.id for delivery in scenario.deliveries]
    vehicle_ids = [vehicle.id for vehicle in scenario.vehicles]
    population = generate_route_population(delivery_ids, len(vehicle_ids), population_size, rng)
    history: List[float] = []
    best_evaluation = None
    stagnant_generations = 0
    valid_stagnant_generations = 0
    generations = range(max_generations) if max_generations is not None else count()

    for generation in generations:
        if stop_requested is not None and stop_requested():
            return
        evaluations = [evaluate_solution(
            scenario,
            repair_routes(scenario, split_variable_solution(individual[0], individual[1], vehicle_ids)),
            capacity_penalty,
            autonomy_penalty,
            priority_penalty,
            critical_penalty,
            critical_position_limit,
        ) for individual in population]
        generation_best = min(evaluations, key=lambda evaluation: evaluation.fitness)

        if best_evaluation is None or generation_best.fitness < best_evaluation.fitness:
            best_evaluation = generation_best
            stagnant_generations = 0
            valid_stagnant_generations = 0
        else:
            stagnant_generations += 1
            if best_evaluation.is_valid:
                valid_stagnant_generations += 1
            else:
                valid_stagnant_generations = 0
        history.append(best_evaluation.fitness)
        yield generation + 1, best_evaluation, list(history)

        if stagnation_limit is not None and stagnant_generations >= stagnation_limit:
            return
        if (
            valid_stability_limit is not None
            and best_evaluation.is_valid
            and valid_stagnant_generations >= valid_stability_limit
        ):
            return

        best_index = min(range(len(evaluations)), key=lambda index: evaluations[index].fitness)
        new_population = [population[best_index]]
        while len(new_population) < population_size:
            parent1 = _tournament(population, evaluations, rng)
            parent2 = _tournament(population, evaluations, rng)
            child_ids = (order_crossover(parent1[0], parent2[0], rng)
                         if rng.random() < crossover_probability else list(parent1[0]))
            child_breakpoints = list(parent1[1] if rng.random() < 0.5 else parent2[1])
            child = mutate_route_plan(
                (child_ids, child_breakpoints), len(vehicle_ids), mutation_probability, rng
            )
            child_ids = mutate_between_vehicles(
                child[0], len(vehicle_ids), vehicle_swap_probability, rng, child[1]
            )
            new_population.append((child_ids, child[1]))
        population = new_population