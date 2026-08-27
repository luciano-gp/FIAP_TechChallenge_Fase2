import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

from vrp_domain import Scenario
from vrp_evaluator import SolutionEvaluation, calculate_distance
from vrp_feasibility import assess_scenario


def build_solution_summary(
    scenario: Scenario,
    evaluation: SolutionEvaluation,
    scenario_name: str = "base",
    history: Optional[Sequence[float]] = None,
    comparison: Optional[Sequence[Mapping[str, Any]]] = None,
    average_speed: Optional[float] = None,
) -> Dict[str, Any]:
    feasibility = assess_scenario(scenario)
    deliveries_by_id = {delivery.id: delivery for delivery in scenario.deliveries}
    priority_counts: Dict[str, int] = {}
    for delivery in scenario.deliveries:
        priority_counts[delivery.priority] = priority_counts.get(delivery.priority, 0) + 1

    vehicles = []
    priority_delivery_positions: Dict[str, List[Dict[str, Any]]] = {}
    for vehicle in scenario.vehicles:
        metrics = evaluation.route_metrics[vehicle.id]
        route = evaluation.routes.get(vehicle.id, [])
        route_details = []
        route_legs = []
        previous_location = scenario.depot.location
        cumulative_distance = 0.0
        for position, delivery_id in enumerate(route, start=1):
            delivery = deliveries_by_id[delivery_id]
            leg_distance = calculate_distance(previous_location, delivery.location)
            cumulative_distance += leg_distance
            route_details.append({
                "position": position,
                "id": delivery.id,
                "priority": delivery.priority,
                "demand": delivery.demand,
                "location": {"x": delivery.x, "y": delivery.y},
                "cumulative_distance": cumulative_distance,
            })
            priority_delivery_positions.setdefault(delivery.priority, []).append({
                "id": delivery.id,
                "vehicle_id": vehicle.id,
                "position": position,
            })
            route_legs.append({
                "from": "depot" if position == 1 else route[position - 2],
                "to": delivery.id,
                "distance": leg_distance,
            })
            previous_location = delivery.location
        return_distance = calculate_distance(previous_location, scenario.depot.location)
        route_legs.append({
            "from": route[-1] if route else "depot",
            "to": "depot",
            "distance": return_distance,
        })
        vehicles.append({
            "id": vehicle.id,
            "route": route,
            "route_details": route_details,
            "route_legs": route_legs,
            "stops": len(route),
            "distance": metrics.distance,
            "load": metrics.load,
            "capacity": vehicle.capacity,
            "capacity_utilization": metrics.load / vehicle.capacity if vehicle.capacity else 0,
            "capacity_excess": metrics.capacity_excess,
            "autonomy": vehicle.autonomy,
            "autonomy_utilization": metrics.distance / vehicle.autonomy if vehicle.autonomy else 0,
            "autonomy_excess": metrics.autonomy_excess,
            "priority_penalty": metrics.priority_penalty,
            "critical_priority_violations": metrics.critical_priority_violations,
            "valid": metrics.is_valid,
        })

    valid_vehicles = sum(vehicle["valid"] for vehicle in vehicles)
    critical_deliveries = priority_counts.get("critical", 0)
    critical_first = sum(
        item["position"] == 1
        for item in priority_delivery_positions.get("critical", [])
    )
    priority_delivery_counts = {
        priority: sum(
            item["priority"] == priority for vehicle in vehicles
            for item in vehicle["route_details"]
        )
        for priority in priority_counts
    }
    total_load = sum(vehicle["load"] for vehicle in vehicles)
    average_vehicle_capacity_utilization = (
        sum(vehicle["capacity_utilization"] for vehicle in vehicles) / len(vehicles)
        if vehicles else 0
    )
    average_vehicle_autonomy_utilization = (
        sum(vehicle["autonomy_utilization"] for vehicle in vehicles) / len(vehicles)
        if vehicles else 0
    )
    recommendations = []
    if not evaluation.is_valid:
        recommendations.append("Revisar as rotas que violam capacidade, autonomia ou prioridade crítica")
    if critical_deliveries and critical_first < critical_deliveries:
        recommendations.append("Atender as entregas críticas antes das demais paradas")
    if any(vehicle["capacity_utilization"] > 0.9 for vehicle in vehicles):
        recommendations.append("Monitorar veículos próximos do limite de capacidade")
    if any(vehicle["autonomy_utilization"] > 0.9 for vehicle in vehicles):
        recommendations.append("Monitorar veículos próximos do limite de autonomia")
    if not recommendations:
        recommendations.append("Solução atende as restrições configuradas")

    summary: Dict[str, Any] = {
        "report": {
            "schema_version": "1.0",
            "purpose": [
                "gerar instrucoes operacionais de entrega",
                "analisar eficiencia da rota",
                "sugerir melhorias logisticas",
            ],
            "data_quality": {
                "all_deliveries_described": not evaluation.missing_delivery_ids,
                "no_duplicate_deliveries": not evaluation.duplicate_delivery_ids,
            },
        },
        "scenario": scenario_name,
        "context": {
            "problem": "roteamento de entregas hospitalares",
            "objective": "minimizar distância e penalizações operacionais",
            "depot": {"x": scenario.depot.x, "y": scenario.depot.y},
            "vehicle_count": len(scenario.vehicles),
            "delivery_count": len(scenario.deliveries),
        },
        "objective": {
            "fitness": evaluation.fitness,
            "total_distance": evaluation.total_distance,
            "penalty": evaluation.penalty,
            "valid": evaluation.is_valid,
        },
        "deliveries": {
            "total": len(scenario.deliveries),
            "by_priority": priority_counts,
            "details": [
                {
                    "id": delivery.id,
                    "priority": delivery.priority,
                    "demand": delivery.demand,
                    "location": {"x": delivery.x, "y": delivery.y},
                }
                for delivery in scenario.deliveries
            ],
            "positions_by_priority": priority_delivery_positions,
            "critical_deliveries": critical_deliveries,
            "critical_deliveries_first": critical_first,
            "served_by_priority": priority_delivery_counts,
            "critical_service_rate": critical_first / critical_deliveries if critical_deliveries else 1,
            "missing_ids": list(evaluation.missing_delivery_ids),
            "duplicate_ids": list(evaluation.duplicate_delivery_ids),
        },
        "vehicles": vehicles,
        "constraints": {
            "scenario_feasible": feasibility.is_feasible,
            "scenario_issues": feasibility.issues,
            "total_demand": feasibility.total_demand,
            "total_fleet_capacity": feasibility.total_capacity,
            "total_autonomy": feasibility.total_autonomy,
            "valid_vehicles": valid_vehicles,
            "vehicle_validity_rate": valid_vehicles / len(vehicles) if vehicles else 0,
            "total_load": total_load,
            "average_capacity_utilization": average_vehicle_capacity_utilization,
            "average_autonomy_utilization": average_vehicle_autonomy_utilization,
        },
        "analysis": {
            "status": "valid" if evaluation.is_valid else "invalid",
            "recommendations": recommendations,
            "operational_summary": (
                "Todas as entregas foram distribuídas em rotas válidas"
                if evaluation.is_valid
                else "A solução possui restrições que exigem revisão operacional"
            ),
        },
    }

    if history:
        summary["evolution"] = {
            "generations": len(history),
            "initial_fitness": history[0],
            "final_fitness": history[-1],
            "improvement": history[0] - history[-1],
            "improvement_rate": (history[0] - history[-1]) / history[0] if history[0] else 0,
        }
    if comparison is not None:
        comparison_rows = [dict(result) for result in comparison]
        summary["comparison"] = comparison_rows
        genetic_fitness = evaluation.fitness
        summary["performance"] = {
            "compared_methods": [row.get("method") for row in comparison_rows],
            "best_compared_fitness": min(
                [genetic_fitness] + [row["fitness"] for row in comparison_rows
                                     if isinstance(row.get("fitness"), (int, float))]
            ),
            "genetic_rank_by_fitness": 1 + sum(
                row.get("fitness", float("inf")) < genetic_fitness
                for row in comparison_rows
            ),
        }
    if average_speed is not None:
        summary["transport"] = {
            "average_speed": average_speed,
            "estimated_total_time": evaluation.total_distance / average_speed
            if average_speed > 0 else None,
            "time_unit": "distance_units_per_hour",
        }
    return summary


def save_solution_summary(summary: Mapping[str, Any], path: str) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
