from src.evaluation.evaluate_rag import RAGEvaluator, EvaluationExample
from src.evaluation.metrics import MockMetric

def test_run():
    # 1. Creamos datos de prueba (Simulando lo que saldría de tu RAG)
    ejemplos = [
        EvaluationExample(
            query="¿Cuál es la carga para fuerza máxima?",
            answer="La NSCA sugiere cargas superiores al 85% del 1RM.",
            contexts=["Capítulo 15: Entrenamiento de resistencia, pág 395."],
            trace_id="test_001"
        ),
        EvaluationExample(
            query="¿Qué es el OIB?",
            answer="Es un término de prueba.",
            contexts=["Documento técnico 1"],
            trace_id="test_002"
        )
    ]

    # 2. Inicializamos el evaluador con nuestra métrica de prueba
    metrics = [MockMetric()]
    evaluator = RAGEvaluator(metrics=metrics)

    # 3. Ejecutamos la evaluación
    print("🚀 Iniciando prueba del Evaluador...")
    report = evaluator.evaluate(ejemplos)
    
    print("✅ Prueba completada con éxito.")

if __name__ == "__main__":
    test_run()