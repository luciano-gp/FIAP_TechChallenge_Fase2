import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

def gerar_instrucoes_llm(json_report_algorithm: dict) -> str:
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.2)
    
    template = """
    Você é o coordenador logístico de um hospital universitário.
    Abaixo estão os resultados do algoritmo genético de roteamento.
    
    Relatório Logístico Bruto (JSON):
    {dados_rotas}
    
    Sua tarefa:
    1. Resuma as métricas principais baseadas no campo 'objective' e os veículos utilizados.
    2. Escreva instruções claras para as equipes de cada veículo com base em 'vehicles.route_details'.
    3. Destaque entregas críticas baseando-se em 'deliveries.critical_deliveries' e apresente as sugestões contidas em 'analysis.recommendations'.
    
    Responda em português (PT-BR) de forma direta e estruturada.
    """
    
    
    resultado = chain.invoke({"dados_rotas": json.dumps(json_report_algorithm, indent=2)})
    return resultado.content

def responder_pergunta_llm(pergunta: str, contexto_json: dict) -> str:
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.2)
    
    template = """
    Você é um assistente logístico. Responda à pergunta do usuário baseando-se EXCLUSIVAMENTE 
    nos dados de roteamento abaixo. Se a informação não estiver no JSON, diga que não sabe.
    
    Dados de Roteamento (JSON):
    {contexto}
    
    Pergunta do Usuário: {pergunta}
    
    Resposta curta e direta:
    """
    prompt = PromptTemplate(input_variables=["contexto", "pergunta"], template=template)
    chain = prompt | llm
    return chain.invoke({"contexto": json.dumps(contexto_json), "pergunta": pergunta}).content