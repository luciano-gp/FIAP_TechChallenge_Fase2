from pydantic import BaseModel

class OptimizationRequest(BaseModel):
    scenario: str = "base"
    generations: int = 150
    population_size: int = 100
    mutation_probability: float = 0.25

class ChatRequest(BaseModel):
    pergunta: str
    contexto_json: dict