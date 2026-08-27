O Tech Challenge é o projeto que engloba os conhecimentos obtidos em todas as disciplinas desta fase. Esta é uma atividade que, a princípio, deve ser desenvolvida em grupo. É importante atentar-se ao prazo de entrega, uma vez que essa atividade é obrigatória, valendo 90% da nota de todas as disciplinas da fase.

## 1. O Desafio: Otimização de Rotas para Distribuição de Medicamentos e Insumos

Após o sucesso inicial no Módulo 1, o sistema hospitalar agora enfrenta desafios logísticos na distribuição eficiente de medicamentos e insumos entre suas diversas unidades e para atendimento domiciliar. 

O desafio é desenvolver um sistema de otimização de rotas utilizando **Algoritmos Genéticos** para resolver esse problema de "caixeiro viajante médico", além de utilizar **Processamento de Linguagem Natural através de LLMs** para gerar relatórios e instruções claras para as equipes de entrega. Este projeto será fundamental para preparar a infraestrutura necessária para o assistente médico mais avançado previsto no Módulo 3.

## 2. Objetivo

Desenvolver um sistema completo de otimização de rotas para entrega de medicamentos e insumos médicos utilizando algoritmos genéticos, em conjunto com a implementação de recursos de processamento de linguagem natural (LLM) para gerar instruções logísticas e relatórios de eficiência.

## 3. Requisitos Obrigatórios e Entregas Técnicas

### 3.1. Sistema de Otimização de Rotas via Algoritmos Genéticos
**Desenvolver um sistema que resolva o problema do caixeiro viajante (TSP) para otimizar rotas:**
*   Implementar a representação genética adequada para rotas.
*   Desenvolver operadores genéticos especializados (seleção, crossover, mutação) para o problema de roteamento.
*   Criar uma função fitness que considere distância, prioridade de entregas e outras restrições relevantes.

**Restrições realistas obrigatórias a serem incluídas:**
*   Prioridades diferentes para entregas (ex: medicamentos críticos vs. insumos regulares).
*   Capacidade limitada de carga dos veículos.
*   Autonomia limitada dos veículos (distância máxima que pode ser percorrida).
*   Múltiplos veículos disponíveis (ampliando o escopo para o Problema de Roteamento de Veículos - VRP).
*   *Outras restrições adicionais que o grupo considerar interessantes para o contexto.*

**Visualização e Base de Código:**
*   Visualizar as rotas otimizadas em um mapa para fácil interpretação.
*   *Observação importante:* Um código base de TSP em Python é fornecido como ponto de partida. Os(as) alunos(as) deverão modificar esse código obrigatoriamente para incorporar as restrições adicionais citadas acima e torná-lo realista para o contexto hospitalar.

### 3.2. Integração com LLMs para Geração de Instruções e Relatórios
Utilizar uma LLM pré-treinada (GPT, Falcon, LLaMA, etc.) para:
*   Gerar instruções detalhadas para motoristas e equipes de entrega com base nas rotas otimizadas.
*   Criar relatórios diários/semanais sobre eficiência de rotas, economia de tempo e recursos.
*   Sugerir melhorias no processo logístico com base nos padrões identificados.
*   Implementar *prompts* eficientes (Prompt Engineering) para extrair informações úteis da LLM.
*   Permitir que o sistema responda a perguntas em linguagem natural sobre as rotas e entregas.

### 3.3. Código e Organização
*   Projeto em Python bem estruturado, utilizando ambiente virtual (Poetry, Pipenv ou venv).
*   Documentação detalhada, incluindo diagramas de arquitetura.
*   Testes automatizados para validação de funcionalidades.
*   *(Opcional / Pontuação Extra)* Se optado pela implementação em nuvem: incluir Infraestrutura como código (IaC) para provisionamento dos recursos, monitoramento e logging adequados.

## 4. Entregáveis da Fase 2

A entrega do projeto deve conter obrigatoriamente os três itens a seguir:

**1. Repositório Git:**
*   Código-fonte completo.
*   Documentação da API (se aplicável).
*   Scripts ou notebooks de demonstração.
*   *(Opcional)* Arquivos de configuração para implantação em nuvem.

**2. Relatório Técnico Explicando:**
*   A implementação do algoritmo genético para roteamento a partir do código base fornecido.
*   As estratégias adotadas para lidar com as restrições adicionais (prioridades, capacidade, autonomia, múltiplos veículos).
*   A integração com LLMs para geração de instruções e relatórios, detalhando a abordagem e os *prompts* utilizados.
*   O comparativo de desempenho com outras abordagens de roteamento.
*   As visualizações e análises das rotas otimizadas.
*   Os desafios enfrentados e as soluções implementadas.
*   *(Opcional)* Arquitetura da solução em nuvem.

**3. Vídeo de Demonstração:**
*   Upload no YouTube ou Vimeo (público ou não listado) de até 15 minutos.
*   Demonstração do sistema em execução.
*   Explicação dos diferentes componentes da solução.
*   Apresentação dos resultados da otimização via algoritmos genéticos.
*   Demonstração prática da integração e funcionamento com as LLMs.
Tech_Challenge_Fase2_Diretrizes.md
Exibindo Tech_Challenge_Fase2_Diretrizes.md.