from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from vrp.vrp_benchmark import run_benchmark
from vrp.vrp_domain import load_scenario
from vrp.vrp_genetic import run_genetic_algorithm

DATA_DIR = ROOT / "data"
SCENARIO_PATH = DATA_DIR / "hospital_scenario.json"
CONFIG_PATH = DATA_DIR / "algorithm_config.json"


def load_config():
    import json
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def save_algorithm_flow(output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 9))
    ax.set_axis_off()

    steps = [
        "Dados do cenário",
        "Parâmetros do algoritmo",
        "População inicial",
        "Avaliação e fitness",
        "Reparo e seleção",
        "Melhor rota",
        "Relatório + LLM",
    ]
    y_positions = [7, 6, 5, 4, 3, 2, 1]
    colors = ["#dbeafe", "#d9f99d", "#fef3c7", "#fce7f3", "#dcfce7", "#e0e7ff", "#fee2e2"]

    for label, y, color in zip(steps, y_positions, colors):
        ax.text(
            1.3, y, label,
            fontsize=10.5,
            ha="center",
            va="center",
            bbox={"boxstyle": "round,pad=0.8", "facecolor": color, "edgecolor": "#475569"},
        )

    for start, end in zip(y_positions, y_positions[1:]):
        ax.annotate(
            "",
            xy=(1.3, end),
            xytext=(1.3, start),
            arrowprops={"arrowstyle": "->", "lw": 1.8, "color": "#334155", "shrinkA": 18, "shrinkB": 18},
        )

    ax.set_xlim(0.4, 2.5)
    ax.set_ylim(0.5, 7.8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def save_route_map(output_path: Path) -> None:
    scenario = load_scenario(str(SCENARIO_PATH))
    config = load_config()
    evaluation, history = run_genetic_algorithm(scenario, **config)

    fig, ax = plt.subplots(figsize=(11, 6))
    priority_color = {
        "critical": "#dc2626",
        "high": "#f59e0b",
        "normal": "#2563eb",
        "low": "#6b7280",
    }

    for delivery in scenario.deliveries:
        ax.scatter(delivery.x, delivery.y, s=85, c=priority_color[delivery.priority], edgecolors="black", linewidth=0.8)
        ax.text(delivery.x + 8, delivery.y + 8, delivery.id, fontsize=8, color="#111827")

    ax.scatter(scenario.depot.x, scenario.depot.y, s=120, c="#111827", marker="s", label="Depósito")
    ax.text(scenario.depot.x + 10, scenario.depot.y + 10, "Depósito", fontsize=9, color="#111827")

    vehicle_handles = []
    for vehicle_id, route in evaluation.routes.items():
        vehicle = next(v for v in scenario.vehicles if v.id == vehicle_id)
        vehicle_rgb = tuple(v / 255 for v in vehicle.color)
        xs = [scenario.depot.x]
        ys = [scenario.depot.y]
        for delivery_id in route:
            delivery = next(d for d in scenario.deliveries if d.id == delivery_id)
            xs.append(delivery.x)
            ys.append(delivery.y)
        xs.append(scenario.depot.x)
        ys.append(scenario.depot.y)
        ax.plot(xs, ys, color=vehicle_rgb, linewidth=2.2, alpha=0.9)
        vehicle_handles.append(Line2D([0], [0], color=vehicle_rgb, linewidth=2.2, label=vehicle_id))

    priority_labels = {"critical": "Crítica", "high": "Alta", "normal": "Normal", "low": "Baixa"}
    priority_handles = [
        Line2D([0], [0], marker="o", linestyle="", markerfacecolor=color, markeredgecolor="black", label=priority_labels[level])
        for level, color in priority_color.items()
    ]

    ax.set_title("Rotas otimizadas por veículo")
    ax.set_xlabel("Coordenada X")
    ax.set_ylabel("Coordenada Y")
    ax.set_aspect("equal")
    ax.grid(True, linestyle="--", alpha=0.25)
    # duas legendas: prioridade das entregas (cor do ponto) e veículo (cor da linha)
    priority_legend = ax.legend(handles=priority_handles, title="Prioridade da\nentrega", loc="upper left", bbox_to_anchor=(1.02, 1), fontsize=8, borderaxespad=0.0)
    ax.add_artist(priority_legend)
    ax.legend(handles=vehicle_handles, title="Veículo", loc="lower left", bbox_to_anchor=(1.02, 0), fontsize=8, borderaxespad=0.0)
    fig.savefig(output_path, dpi=220, bbox_inches="tight", bbox_extra_artists=[priority_legend])
    plt.close(fig)


def save_benchmark_chart(output_path: Path) -> None:
    scenario = load_scenario(str(SCENARIO_PATH))
    config = load_config()
    results = run_benchmark(scenario, config, scenario_name="base")
    labels = [result.method for result in results]
    fitness = [result.evaluation.fitness for result in results]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(labels, fitness, color=["#60a5fa", "#34d399", "#fbbf24"], edgecolor="black")
    for bar, value in zip(bars, fitness):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 400, f"{value:.1f}", ha="center", va="bottom", fontsize=9)
    ax.set_title("Comparativo de desempenho entre estratégias")
    ax.set_ylabel("Fitness")
    ax.grid(axis="y", linestyle="--", alpha=0.2)
    fig.tight_layout()
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    output_dir = Path(__file__).resolve().parent
    output_dir.mkdir(parents=True, exist_ok=True)

    save_algorithm_flow(output_dir / "optimization_flow.png")
    save_route_map(output_dir / "optimized_routes.png")
    save_benchmark_chart(output_dir / "performance_comparison.png")

    print(f"Imagens salvas em: {output_dir}")


if __name__ == "__main__":
    main()
