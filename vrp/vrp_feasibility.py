from dataclasses import dataclass
from typing import List

from vrp.vrp_domain import Scenario
from vrp.vrp_evaluator import calculate_distance


@dataclass(frozen=True)
class FeasibilityReport:
    total_demand: float
    total_capacity: float
    critical_deliveries: int
    vehicle_count: int
    minimum_round_trip_distance: float
    total_autonomy: float
    issues: List[str]

    @property
    def is_feasible(self) -> bool:
        return not self.issues


def assess_scenario(scenario: Scenario) -> FeasibilityReport:
    # Verifica se o cenário tem capacidade e autonomia mínimos para ser viável.
    total_demand = sum(delivery.demand for delivery in scenario.deliveries)
    total_capacity = sum(vehicle.capacity for vehicle in scenario.vehicles)
    critical_deliveries = sum(
        delivery.priority == "critical" for delivery in scenario.deliveries
    )
    minimum_round_trip_distance = sum(
        2 * calculate_distance(scenario.depot.location, delivery.location)
        for delivery in scenario.deliveries
    )
    total_autonomy = sum(vehicle.autonomy for vehicle in scenario.vehicles)
    issues = []

    if total_demand > total_capacity:
        issues.append("A demanda total excede a capacidade total da frota")
    if any(delivery.demand > max((vehicle.capacity for vehicle in scenario.vehicles), default=0)
           for delivery in scenario.deliveries):
        issues.append("Existe uma entrega maior que a capacidade de qualquer veículo")
    if critical_deliveries > len(scenario.vehicles):
        issues.append("Existem mais entregas críticas que veículos disponíveis")
    return FeasibilityReport(
        total_demand=total_demand,
        total_capacity=total_capacity,
        critical_deliveries=critical_deliveries,
        vehicle_count=len(scenario.vehicles),
        minimum_round_trip_distance=minimum_round_trip_distance,
        total_autonomy=total_autonomy,
        issues=issues,
    )
