from typing import Dict, List

from vrp.vrp_domain import Delivery, Scenario
from vrp.vrp_evaluator import calculate_distance


def _route_distance(scenario: Scenario, deliveries: List[Delivery]) -> float:
    points = [scenario.depot.location]
    points.extend(delivery.location for delivery in deliveries)
    points.append(scenario.depot.location)
    return sum(calculate_distance(current, following)
               for current, following in zip(points, points[1:]))


def _delivery_map(scenario: Scenario) -> Dict[str, Delivery]:
    return {delivery.id: delivery for delivery in scenario.deliveries}


def _best_insertion_distance(
    scenario: Scenario, route: List[Delivery], delivery: Delivery
) -> float:
    return min(
        _route_distance(scenario, route[:index] + [delivery] + route[index:])
        for index in range(len(route) + 1)
    )


def repair_routes(scenario: Scenario, routes: Dict[str, List[str]]) -> Dict[str, List[str]]:
    deliveries = _delivery_map(scenario)
    repaired = {vehicle.id: [] for vehicle in scenario.vehicles}
    assigned = set()

    for vehicle in scenario.vehicles:
        for delivery_id in routes.get(vehicle.id, []):
            if delivery_id in deliveries and delivery_id not in assigned:
                repaired[vehicle.id].append(delivery_id)
                assigned.add(delivery_id)

    missing = [delivery.id for delivery in scenario.deliveries if delivery.id not in assigned]
    for delivery_id in missing:
        vehicle_id = min(repaired, key=lambda key: len(repaired[key]))
        repaired[vehicle_id].append(delivery_id)

    critical_ids = [
        delivery.id for delivery in scenario.deliveries
        if delivery.priority == "critical"
    ]
    for critical_id in critical_ids:
        for route in repaired.values():
            if critical_id in route:
                route.remove(critical_id)
    for vehicle, critical_id in zip(scenario.vehicles, critical_ids):
        repaired[vehicle.id].insert(0, critical_id)
    if len(critical_ids) > len(scenario.vehicles):
        for critical_id in critical_ids[len(scenario.vehicles):]:
            target_id = min(repaired, key=lambda key: len(repaired[key]))
            repaired[target_id].insert(0, critical_id)

    for vehicle in scenario.vehicles:
        while True:
            route = repaired[vehicle.id]
            route_deliveries = [deliveries[delivery_id] for delivery_id in route]
            load = sum(delivery.demand for delivery in route_deliveries)
            distance = _route_distance(scenario, route_deliveries)
            if load <= vehicle.capacity and distance <= vehicle.autonomy:
                break

            movable = [
                delivery_id for delivery_id in route[1:]
                if deliveries[delivery_id].priority != "critical"
            ]
            if not movable:
                break
            candidates = []
            current_distance = _route_distance(
                scenario, [deliveries[item] for item in route]
            )
            for delivery_id in movable:
                delivery = deliveries[delivery_id]
                for target in scenario.vehicles:
                    if target.id == vehicle.id:
                        continue
                    target_deliveries = [deliveries[item] for item in repaired[target.id]]
                    target_load = sum(item.demand for item in target_deliveries)
                    if target_load + delivery.demand > target.capacity:
                        continue
                    candidate_distance = _best_insertion_distance(
                        scenario, target_deliveries, delivery
                    )
                    if candidate_distance <= target.autonomy:
                        candidates.append((
                            candidate_distance - current_distance,
                            candidate_distance,
                            delivery_id,
                            target.id,
                        ))
            if not candidates:
                break
            _, _, delivery_id, target_id = min(candidates)
            repaired[vehicle.id].remove(delivery_id)
            repaired[target_id].append(delivery_id)

    return repaired