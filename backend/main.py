from fastapi import FastAPI, HTTPException

from backend.schemas import OptimizationRequest, ChatRequest
from backend.llm_agent import gerar_instrucoes_llm, responder_pergunta_llm
from backend.api_bridge import executar_vrp_api

app = FastAPI(title="API Otimização VRP - Tech Challenge")


@app.post("/chat")
async def chat_logistico(req: ChatRequest):
    """
    Endpoint para responder perguntas logísticas baseadas no contexto do JSON de roteamento.
    """
    try:
        resposta = responder_pergunta_llm(req.pergunta, req.contexto_json)
        return {"resposta": resposta}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/otimizar")
async def otimizar_rotas(req: OptimizationRequest):
    """
    Endpoint para otimizar rotas usando o algoritmo genético e gerar um relatório em linguagem natural.
    """
    try:
        #Aciona a ponte de integração com o código VRP
        json_report = executar_vrp_api(
            scenario_name=req.scenario,
            generations=req.generations,
            pop_size=req.population_size,
            mut_prob=req.mutation_probability
        )
        
        # Injeta o JSON completo na LLM do Gemini
        relatorio_ia = gerar_instrucoes_llm(json_report)
        
        return {
            "dados_brutos": json_report,
            "relatorio_ia": relatorio_ia
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))