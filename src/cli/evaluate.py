"""Script definitivo para evaluar el sistema RAG con métricas de la NSCA."""

import argparse
import json
import sys
import os
from datetime import datetime
from pathlib import Path

# 1. Configuración de rutas (Doble Path para evitar ModuleNotFoundError)
root_path = Path(__file__).resolve().parent.parent
sys.path.append(str(root_path))
sys.path.append(str(root_path / "src"))

# 2. Imports de Observabilidad y Configuración
from langfuse import observe
from langfuse.openai import OpenAI
from rich.console import Console

from src.config import settings
from src.evaluation_core.evaluator import EvaluationExample, RAGEvaluator
from src.evaluation_core.llm_judge import LLMJudge
from src.evaluation_core.metrics import (
    AnswerRelevanceMetric,
    ContextRelevanceMetric,
    FaithfulnessMetric,
)
from src.observability.langfuse_client import configure_langfuse, flush_langfuse

console = Console()

# Inicializamos configuración de Langfuse
configure_langfuse()

def load_evaluation_examples(examples_file: Path) -> list[EvaluationExample]:
    """Carga los ejemplos del dataset generado (JSON)."""
    if not examples_file.exists():
        raise FileNotFoundError(f"No se encuentra el archivo: {examples_file}")
        
    with open(examples_file, "r", encoding='utf-8') as f:
        data = json.load(f)

    # Convertimos cada diccionario del JSON en un objeto de evaluación
    return [EvaluationExample(**example) for example in data]

@observe(name="nsca-rag-evaluation")
def run_evaluation(examples_file: Path, output_dir: Path):
    """Ejecuta el proceso de evaluación y genera el reporte."""
    
    try:
        console.print(f"[bold blue]🧪 Cargando dataset desde {examples_file}...[/]")
        examples = load_evaluation_examples(examples_file)
        console.print(f"[green]✅ {len(examples)} ejemplos listos para evaluar.[/]\n")

        # Configuramos el Juez (Groq) usando tus Settings
        llm_client = OpenAI(
            api_key=settings.groq_api_key,
            base_url=settings.groq_base_url,
        )

        llm_judge = LLMJudge(
            client=llm_client,
            model_name=settings.groq_judge_model_name or settings.groq_model_name,
            temperature=0.0,
        )

        # Definimos la Tríada RAG para validar los protocolos NSCA
        metrics = [
            FaithfulnessMetric(llm_judge),      # ¿La respuesta está en el PDF?
            AnswerRelevanceMetric(llm_judge),   # ¿Responde a lo que pidió el coach?
            ContextRelevanceMetric(llm_judge),  # ¿El chunk del PDF es el correcto?
        ]

        # Creamos el evaluador y lanzamos el proceso
        evaluator = RAGEvaluator(metrics=metrics)
        for example in examples[:2]:
            console.print(f"[yellow]Analizando Query:[/]: {example.query}")
        report = evaluator.evaluate(evaluation_examples=examples)

        # Guardar reporte local con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"report_nsca_{timestamp}.json"

        with open(output_path, "w", encoding='utf-8') as f:
            json.dump(report.model_dump(), f, indent=2, ensure_ascii=False)

        console.print(f"\n[bold green]🏆 Evaluación completada con éxito![/]")
        console.print(f"[yellow]Reporte guardado en: {output_path}[/]\n")

    except Exception as e:
        console.print(f"[bold red]❌ Error durante la evaluación: {e}[/]")

def main():
    parser = argparse.ArgumentParser(description="Evaluador oficial del Proyecto Final IPA")
    parser.add_argument("--file", type=str, default="Evaluations/eval_dataset.json")
    parser.add_argument("--out", type=str, default="Evaluations/results")
    args = parser.parse_args()

    run_evaluation(Path(args.file), Path(args.out))
    
    # Aseguramos que los resultados suban a Langfuse
    flush_langfuse()

if __name__ == "__main__":
    main()