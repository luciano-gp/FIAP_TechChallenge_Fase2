# Otimizador de Rotas Hospitalares

Projeto desenvolvido para o Tech Challenge da Fase 2 da FIAP. O sistema utiliza algoritmos genéticos para otimizar rotas de entrega de medicamentos e insumos hospitalares.

O projeto possui duas implementações:

- **TSP original:** versão inicial do problema do caixeiro viajante, mantida para comparação.
- **VRP otimizado:** versão hospitalar com múltiplos veículos, prioridades, capacidade de carga e autonomia.

## Requisitos

- Python 3.9.
- Conda.
- Sistema operacional com suporte ao Pygame.

As dependências estão declaradas em [environment.yml](environment.yml).

## Instalação

Na pasta do projeto, crie o ambiente Conda:

```bash
conda env create --file environment.yml
```

Ative o ambiente:

```bash
conda activate fiap_tsp
```

Para atualizar um ambiente já existente:

```bash
conda env update --file environment.yml --prune
```

## Execução

O ponto de entrada é [main.py](main.py). O modo otimizado é executado por padrão:

```bash
python main.py
```

Para executar explicitamente o VRP hospitalar:

```bash
python main.py --mode vrp
```

Para visualizar um cenário específico em tempo real:

```bash
python main.py --mode vrp --scenario alta_demanda --generations 1000
```

Cenários disponíveis: `base`, `alta_prioridade`, `alta_demanda`, `baixa_autonomia`, `frota_reduzida`, `maior`, `capacidade_insuficiente` e `autonomia_insuficiente`.

O vizinho mais próximo é determinístico e também passa pelo reparo de rotas antes da avaliação. Em cenários fisicamente inviáveis, como demanda superior à capacidade disponível ou autonomia insuficiente, a solução permanece inválida e a penalização é preservada.

Para executar o TSP original:

```bash
python main.py --mode tsp
```

Também é possível executar os arquivos diretamente:

```bash
python -m tsp_base.tsp
python -m vrp.vrp_app
```

Durante a execução, pressione `Q` ou feche a janela para encerrar o programa.

### Limite de gerações

É possível definir um limite de gerações para comparar as implementações em condições equivalentes:

```bash
python main.py --mode tsp --generations 1000
python main.py --mode vrp --generations 1000
```

Sem o parâmetro `--generations`, a execução continua até o usuário pressionar `Q`.

### Visualização por cenário

O modo otimizado permite visualizar os cenários disponíveis em tempo real. A janela mostra o mapa, as rotas, a sequência de entregas, as prioridades, os indicadores dos veículos e a evolução do fitness.

```bash
python main.py --mode vrp --scenario base --generations 1000
python main.py --mode vrp --scenario alta_prioridade --generations 1000
python main.py --mode vrp --scenario alta_demanda --generations 1000
python main.py --mode vrp --scenario baixa_autonomia --generations 1000
python main.py --mode vrp --scenario frota_reduzida --generations 1000
python main.py --mode vrp --scenario maior --generations 1000
```

Para deixar a simulação rodando até o usuário pressionar `Q`, omita o limite:

```bash
python main.py --mode vrp --scenario alta_demanda
```

Ao finalizar cada execução do modo `vrp`, o sistema monta um report estruturado em formato JSON, com os dados da solução, das entregas, dos veículos, das restrições e da evolução. O arquivo é salvo automaticamente em `results/vrp_report_<cenario>.json`.

Os arquivos CSV gerados pelo benchmark são independentes desse report JSON e continuam sendo salvos na pasta `results/`.

## Benchmark

O benchmark compara três estratégias de roteamento:

- Rota aleatória.
- Vizinho mais próximo.
- Algoritmo genético.

Execute, por exemplo:

```bash
python -m vrp.vrp_benchmark --repetitions 10 --generations 1000
```

Para executar todos os cenários disponíveis:

```bash
python -m vrp.vrp_benchmark --scenarios base alta_prioridade alta_demanda baixa_autonomia frota_reduzida maior --repetitions 10 --generations 1000
```

Os cenários variam a quantidade de entregas, prioridades, demandas, autonomia e tamanho da frota.

Os resultados são salvos automaticamente na pasta `results/`:

- `results/benchmark_results.csv`: dados de cada execução.
- `results/benchmark_results_summary.csv`: resumo estatístico por método.
- `results/benchmark_results_evolution.csv`: melhor fitness registrado a cada geração.

O resumo separa `mean_distance`, `mean_penalty` e `mean_fitness`, permitindo distinguir a distância física das penalizações por restrições.

Também é possível escolher o arquivo de saída:

```bash
python -m vrp.vrp_benchmark --repetitions 10 --generations 1000 --output resultados.csv
```

Nesse caso, os arquivos serão salvos como `results/resultados.csv` e `results/resultados_summary.csv`.

Para executar todos os cenários:

```bash
python -m vrp.vrp_benchmark \
	--scenarios base alta_prioridade alta_demanda baixa_autonomia frota_reduzida maior \
	--repetitions 10 \
	--generations 1000 \
	--output benchmark_results_all.csv
```

Esse comando gera 126 registros detalhados e 18 linhas de resumo, salvando os arquivos em:

```text
results/benchmark_results_all.csv
results/benchmark_results_all_summary.csv
```

Para uma execução rápida de validação:

```bash
python -m vrp.vrp_benchmark --scenarios base --repetitions 1 --generations 5 --output benchmark_smoke.csv
```

## Testes

Execute os testes automatizados com:

```bash
python -m unittest -v vrp/test_vrp.py
```

Para executar apenas os testes sem detalhes:

```bash
python -m unittest -q vrp/test_vrp.py
```

Para verificar a sintaxe dos módulos Python:

```bash
python -m py_compile main.py \
	vrp/vrp_app.py vrp/vrp_domain.py vrp/vrp_evaluator.py vrp/vrp_repair.py \
	vrp/vrp_genetic.py vrp/vrp_benchmark.py vrp/vrp_scenarios.py vrp/test_vrp.py \
	tsp_base/tsp.py tsp_base/__init__.py tsp_base/genetic_algorithm.py \
	tsp_base/draw_functions.py tsp_base/benchmark_att48.py
```

## Dados e configuração

O cenário hospitalar e os parâmetros do algoritmo ficam separados do código:

- [data/scenarios.json](data/scenarios.json): alterações aplicadas sobre o cenário-base.

## Arquivos principais

- [main.py](main.py): seleciona a implementação que será executada.
- [tsp_base/tsp.py](tsp_base/tsp.py): implementação original do TSP.
- [tsp_base/](tsp_base/): módulos, benchmark, demos e imagens exclusivos do TSP original.
- [vrp/vrp_app.py](vrp/vrp_app.py): execução e visualização do VRP hospitalar.
- [vrp/vrp_domain.py](vrp/vrp_domain.py): modelos e carregamento dos dados.
- [vrp/vrp_genetic.py](vrp/vrp_genetic.py): algoritmo genético.
- [vrp/vrp_evaluator.py](vrp/vrp_evaluator.py): avaliação das rotas e restrições.
- [vrp/vrp_repair.py](vrp/vrp_repair.py): reparo de soluções inválidas.
- [vrp/vrp_feasibility.py](vrp/vrp_feasibility.py): diagnóstico de viabilidade dos cenários.
- [vrp/vrp_reporting.py](vrp/vrp_reporting.py): resumo estruturado das soluções para integração futura.
- [vrp/vrp_benchmark.py](vrp/vrp_benchmark.py): comparação entre estratégias.
- [vrp/test_vrp.py](vrp/test_vrp.py): testes automatizados.

## Report para integração com LLM

O modo `vrp` monta, ao final de cada execução, um report JSON em memória por meio de `build_solution_summary()` em [vrp_reporting.py](vrp_reporting.py). Esse report não é salvo automaticamente.

O payload contém dados para três usos:

- **Instruções de entrega:** rota ordenada, posição, ID, prioridade, demanda, localização e distância de cada trecho.
- **Relatórios de eficiência:** fitness, distância, penalizações, utilização de capacidade e autonomia, evolução por geração, tempo estimado e validade.
- **Sugestões logísticas:** violações, entregas críticas, gargalos de capacidade/autonomia, diagnóstico de viabilidade, taxa de validade e recomendações factuais.

O campo `comparison` pode receber os resultados de outros métodos, como vizinho mais próximo, para que a LLM compare desempenho. O campo `transport` pode receber uma velocidade média para estimar o tempo total da rota.

## Integrantes
Cristofer Gaier Sais (rm374802)


Luciano Gomes Pereira Júnior (rm374898)
