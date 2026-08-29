import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.append(str(ROOT))

from vrp.vrp_scenarios import load_benchmark_scenarios
from vrp.vrp_domain import load_algorithm_config
from vrp.vrp_genetic import run_genetic_algorithm
from vrp.vrp_reporting import build_solution_summary

def executar_vrp_api(scenario_name: str, generations: int, pop_size: int, mut_prob: float):
    # Carrega cenários configurados em data/scenarios.json e data/hospital_scenario.json
    scenarios = load_benchmark_scenarios(str(ROOT / "data" / "hospital_scenario.json")) 
    
    if scenario_name not in scenarios:
        scenario_name = "base"
        
    scenario = scenarios[scenario_name]
    config = load_algorithm_config(str(ROOT / "data" / "algorithm_config.json"))
    
    # Sobrescreve as configurações padrão com os parâmetros da requisição
    config["max_generations"] = generations
    config["population_size"] = pop_size
    config["mutation_probability"] = mut_prob

    # Executa o algoritmo genético para otimização do VRP
    evaluation, history = run_genetic_algorithm(scenario, **config)
    
    # Gera o relatório JSON com os resultados da avaliação da solução
    json_report = build_solution_summary(scenario, evaluation, scenario_name, history)
    
    return json_report