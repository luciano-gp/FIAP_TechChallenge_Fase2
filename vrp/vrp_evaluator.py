from dataclasses import dataclass
import math
from typing import Dict, List, Mapping, Tuple

from vrp.vrp_domain import Delivery, Scenario, Vehicle


PRIORITY_WEIGHTS = {
    "critical": 4.0,
    "high": 3.0,
    "normal": 1.0,
    "low": 0.5,
}


@dataclass(frozen=True)
class RouteMetrics:
    vehicle_id: str
    distance: float
    load: float
    capacity_excess: float
    autonomy_excess: float
    priority_penalty: float
    critical_priority_violations: int

    @property
    def is_valid(self) -> bool:
        return (
            self.capacity_excess == 0
            and self.autonomy_excess == 0
            and self.critical_priority_violations == 0
        )


@dataclass(frozen=True)
class SolutionEvaluation:
    routes: Dict[str, List[str]]
    route_metrics: Dict[str, RouteMetrics]
    total_distance: float
    penalty: float
    fitness: float
    missing_delivery_ids: Tuple[str, ...]
    duplicate_delivery_ids: Tuple[str, ...]

    @property
    def is_valid(self) -> bool:
        return (
            not self.missing_delivery_ids
            and not self.duplicate_delivery_ids
            and all(metrics.is_valid for metrics in self.route_metrics.values())
        )


def calculate_distance(
    point1: Tuple[float, float], point2: Tuple[float, float]
) -> float:
    return math.hypot(point1[0] - point2[0], point1[1] - point2[1])


def _route_distance(scenario: Scenario, deliveries: List[Delivery]) -> float:
    points = [scenario.depot.location]
    points.extend(delivery.location for delivery in deliveries)
    points.append(scenario.depot.location)
    return sum(calculate_distance(current, following)
               for current, following in zip(points, points[1:]))


def evaluate_solution(
    scenario: Scenario,
    routes: Mapping[str, List[str]],
    capacity_penalty: float = 10000,
    autonomy_penalty: float = 10000,
    priority_penalty: float = 100,
    critical_penalty: float = 100000,
    critical_position_limit: int = 1,
) -> SolutionEvaluation:
    deliveries_by_id = {delivery.id: delivery for delivery in scenario.deliveries}
    vehicles_by_id = {vehicle.id: vehicle for vehicle in scenario.vehicles}
    seen_ids: List[str] = []
    route_metrics: Dict[str, RouteMetrics] = {}
    normalized_routes: Dict[str, List[str]] = {}
    total_penalty = 0.0

    for vehicle in scenario.vehicles:
        delivery_ids = list(routes.get(vehicle.id, []))
        normalized_routes[vehicle.id] = delivery_ids
        deliveries = [deliveries_by_id[delivery_id]
                      for delivery_id in delivery_ids
                      if delivery_id in deliveries_by_id]
        seen_ids.extend(delivery_ids)

        load = sum(delivery.demand for delivery in deliveries)
        distance = _route_distance(scenario, deliveries)
        capacity_excess = max(0.0, load - vehicle.capacity)
        autonomy_excess = max(0.0, distance - vehicle.autonomy)
        route_priority_penalty = sum(
            PRIORITY_WEIGHTS.get(delivery.priority, 1.0) * position
            for position, delivery in enumerate(deliveries, start=1)
        )
        critical_priority_violations = sum(
            delivery.priority == "critical"
            and position > critical_position_limit
            for position, delivery in enumerate(deliveries, start=1)
        )

        metrics = RouteMetrics(
            vehicle_id=vehicle.id,
            distance=distance,
            load=load,
            capacity_excess=capacity_excess,
            autonomy_excess=autonomy_excess,
            priority_penalty=route_priority_penalty,
            critical_priority_violations=critical_priority_violations,
        )
        route_metrics[vehicle.id] = metrics
        total_penalty += (
            capacity_excess * capacity_penalty
            + autonomy_excess * autonomy_penalty
            + route_priority_penalty * priority_penalty
            + critical_priority_violations * critical_penalty
        )

    expected_ids = set(deliveries_by_id)
    seen_id_set = set(seen_ids)
    missing_ids = tuple(sorted(expected_ids - seen_id_set))
    duplicate_ids = tuple(sorted({delivery_id for delivery_id in seen_ids
                                   if seen_ids.count(delivery_id) > 1}))
    structural_penalty = (len(missing_ids) + len(duplicate_ids)) * capacity_penalty

    total_distance = sum(metrics.distance for metrics in route_metrics.values())
    total_penalty += structural_penalty
    return SolutionEvaluation(
        routes=normalized_routes,
        route_metrics=route_metrics,
        total_distance=total_distance,
        penalty=total_penalty,
        fitness=total_distance + total_penalty,
        missing_delivery_ids=missing_ids,
        duplicate_delivery_ids=duplicate_ids,
    )