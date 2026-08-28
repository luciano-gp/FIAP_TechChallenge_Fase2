from fastapi import FastAPI, HTTPException
from schemas import OptimizationRequest, ChatRequest
from llm_agent import gerar_instrucoes_llm, responder_pergunta_llm
from api_bridge import executar_vrp_api

app = FastAPI(title="API Otimização VRP - Tech Challenge")

@app.post("/chat")
async def chat_logistico(req: ChatRequest):
    try:
        resposta = responder_pergunta_llm(req.pergunta, req.contexto_json)
        return {"resposta": resposta}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/otimizar")
async def otimizar_rotas(req: OptimizationRequest):
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