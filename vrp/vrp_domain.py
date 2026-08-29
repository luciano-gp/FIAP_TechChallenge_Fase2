from dataclasses import dataclass
from pathlib import Path
import json
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class Delivery:
    id: str
    x: float
    y: float
    demand: float
    priority: str

    @property
    def location(self) -> Tuple[float, float]:
        return self.x, self.y


@dataclass(frozen=True)
class Vehicle:
    id: str
    capacity: float
    autonomy: float
    color: Tuple[int, int, int]


@dataclass(frozen=True)
class Depot:
    x: float
    y: float

    @property
    def location(self) -> Tuple[float, float]:
        return self.x, self.y


@dataclass(frozen=True)
class Scenario:
    depot: Depot
    deliveries: List[Delivery]
    vehicles: List[Vehicle]


def load_scenario(path: str) -> Scenario:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    depot = Depot(**data["depot"])
    deliveries = [Delivery(**delivery) for delivery in data["deliveries"]]
    vehicles = [
        Vehicle(
            id=vehicle["id"],
            capacity=vehicle["capacity"],
            autonomy=vehicle["autonomy"],
            color=tuple(vehicle["color"]),
        )
        for vehicle in data["vehicles"]
    ]
    return Scenario(depot=depot, deliveries=deliveries, vehicles=vehicles)


def load_algorithm_config(path: str) -> Dict[str, float]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
