from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_otimizar_endpoint_valido():
    # Testa se a API responde corretamente com um cenário conhecido
    payload = {
        "scenario": "base",
        "generations": 2, 
        "population_size": 10,
        "mutation_probability": 0.1
    }
    response = client.post("/otimizar", json=payload)
    assert response.status_code == 200
    dados = response.json()
    
    # Verifica a estrutura do contrato de dados
    assert "dados_brutos" in dados
    assert "relatorio_ia" in dados
    assert "objective" in dados["dados_brutos"]

def test_chat_endpoint_sem_contexto():
    # Testa a validação do Pydantic (deve falhar por falta de dados estruturados)
    response = client.post("/chat", json={"pergunta": "Qual a distância?"})
    assert response.status_code == 422 # Unprocessable Entity