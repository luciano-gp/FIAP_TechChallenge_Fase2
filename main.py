import argparse
import subprocess
import sys
from pathlib import Path
from vrp_scenarios import SCENARIO_NAMES


ROOT = Path(__file__).parent


def run_tsp() -> int:
    return subprocess.call([sys.executable, "-m", "tsp_base.tsp"], cwd=ROOT)


def run_vrp() -> int:
    return subprocess.call([sys.executable, str(ROOT / "vrp.py")], cwd=ROOT)


def main() -> int:
    parser = argparse.ArgumentParser(description="Seleciona a implementacao TSP ou VRP")
    parser.add_argument(
        "--mode",
        choices=("tsp", "vrp"),
        default="vrp",
        help="Implementacao a executar (padrao: vrp)",
    )
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
        help="Cenario para o modo vrp",
    )
    args = parser.parse_args()

    if args.mode == "tsp":
        command = [sys.executable, "-m", "tsp_base.tsp"]
    else:
        command = [sys.executable, str(ROOT / "vrp.py")]
    if args.generations is not None:
        command.extend(["--generations", str(args.generations)])
    if args.mode == "vrp":
        command.extend(["--scenario", args.scenario])
    return subprocess.call(command, cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
