from pydantic import BaseModel
from abc import ABC, abstractmethod

class MetricResult(BaseModel):
    score: float
    reasoning: str

class Metric(ABC):
    @abstractmethod
    def evaluate(self, query: str, answer: str, contexts: list[str]) -> MetricResult:
        pass

class MockMetric(Metric):
    """Métrica de prueba que simula una evaluación."""
    def evaluate(self, query: str, answer: str, contexts: list[str]) -> MetricResult:
        # Simulamos que si la respuesta es larga, es buena
        score = min(1.0, len(answer) / 50)
        return MetricResult(
            score=score, 
            reasoning="Prueba técnica: Evaluación basada en longitud de respuesta."
        )