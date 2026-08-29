import json
from dataclasses import replace
from pathlib import Path
from typing import Dict

from vrp.vrp_domain import Delivery, Scenario, load_scenario


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
# Carrega variações do cenário base para benchmark e testes de robustez.
SCENARIO_PATH = DATA_DIR / "hospital_scenario.json"
SCENARIOS_CONFIG_PATH = DATA_DIR / "scenarios.json"
SCENARIO_NAMES = tuple(
    json.loads(SCENARIOS_CONFIG_PATH.read_text(encoding="utf-8"))
)


def _apply_definition(base: Scenario, definition: dict) -> Scenario:
    # Ajusta a demanda, prioridades e frota conforme uma definição de cenário alternativo.
    deliveries = list(base.deliveries)
    priority_replacements = definition.get("delivery_priority_replacements", {})
    priority_by_id = definition.get("delivery_priority_by_id", {})
    deliveries = [
        replace(
            delivery,
            demand=round(delivery.demand * definition.get("delivery_demand_multiplier", 1), 2),
            priority=priority_by_id.get(
                delivery.id,
                priority_replacements.get(delivery.priority, delivery.priority),
            ),
        )
        for delivery in deliveries
    ]
    deliveries.extend(Delivery(**delivery) for delivery in definition.get("extra_deliveries", []))

    vehicles = list(base.vehicles)
    vehicle_count = definition.get("vehicle_count", len(vehicles))
    vehicles = vehicles[:vehicle_count]
    vehicle_overrides = definition.get("vehicle_overrides", {})
    vehicles = [replace(vehicle, **vehicle_overrides) for vehicle in vehicles]
    return replace(base, deliveries=deliveries, vehicles=vehicles)


def load_benchmark_scenarios(path: str = str(SCENARIO_PATH)) -> Dict[str, Scenario]:
    # Monta os cenários de benchmark usados em comparação entre estratégias de solução.
    base = load_scenario(path)
    definitions = json.loads(SCENARIOS_CONFIG_PATH.read_text(encoding="utf-8"))
    return {
        name: _apply_definition(base, definition)
        for name, definition in definitions.items()
    }
