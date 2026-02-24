import os
import statistics
import time
from datetime import datetime
from pydantic import BaseModel
from rich.console import Console
from rich.table import Table
from tqdm import tqdm

# Intentamos importar langfuse, si no está instalado, fallará silenciosamente o usaremos un mock
try:
    from langfuse import get_client
except ImportError:
    get_client = None

console = Console()

# --- MODELOS DE DATOS ---

class EvaluationExample(BaseModel):
    """Ejemplo individual para evaluación."""
    query: str
    answer: str
    contexts: list[str]
    trace_id: str | None = None

class MetricStatistics(BaseModel):
    """Resumen estadístico de una métrica."""
    mean: float
    std_dev: float
    min: float
    max: float
    median: float
    count_below_50: int
    percent_below_50: float
    # Simplificado para evitar errores de percentiles con pocos datos
    count_above_70: int
    percent_above_70: float

class MetricReport(BaseModel):
    """Reporte de una métrica específica."""
    metric_name: str
    average_score: float
    statistics: MetricStatistics
    individual_scores: list[float]
    individual_reasoning: list[str]
    duration_seconds: float

class QueryLevelResult(BaseModel):
    """Resultados por cada pregunta individual."""
    query_index: int
    query: str
    metric_scores: dict[str, float]
    overall_score: float

class EvaluationReport(BaseModel):
    """Reporte final completo."""
    timestamp: str
    num_examples: int
    total_duration_seconds: float
    metric_reports: list[MetricReport]
    query_level_results: list[QueryLevelResult]

# --- CLASE PRINCIPAL DEL EVALUADOR ---

class RAGEvaluator:
    """Evaluador para sistemas RAG usando múltiples métricas."""

    def __init__(self, metrics: list):
        self.metrics = metrics

    def evaluate(self, evaluation_examples: list[EvaluationExample]) -> EvaluationReport:
        start_time = time.time()
        console.print(f"\n[bold blue]Evaluando {len(evaluation_examples)} ejemplos...[/]\n")

        metric_reports = []
        all_scores = {}

        for metric in self.metrics:
            metric_name = metric.__class__.__name__
            metric_start_time = time.time()
            console.print(f"[yellow]Ejecutando {metric_name}...[/]")

            scores, reasoning = [], []

            for example in tqdm(evaluation_examples, desc=f"  {metric_name}"):
                result = metric.evaluate(
                    query=example.query,
                    answer=example.answer,
                    contexts=example.contexts
                )
                scores.append(result.score)
                reasoning.append(result.reasoning)

                # Envío a Langfuse si el cliente existe y hay trace_id
                if get_client and example.trace_id:
                    try:
                        get_client().create_score(
                            name=metric_name,
                            value=result.score,
                            trace_id=example.trace_id,
                            comment=result.reasoning
                        )
                    except:
                        pass

            duration = time.time() - metric_start_time
            stats = self._calculate_statistics(scores)
            all_scores[metric_name] = scores

            metric_reports.append(MetricReport(
                metric_name=metric_name,
                average_score=sum(scores)/len(scores),
                statistics=stats,
                individual_scores=scores,
                individual_reasoning=reasoning,
                duration_seconds=duration
            ))

        query_results = self._create_query_level_results(evaluation_examples, all_scores)
        total_duration = time.time() - start_time

        report = EvaluationReport(
            timestamp=datetime.now().isoformat(),
            num_examples=len(evaluation_examples),
            total_duration_seconds=total_duration,
            metric_reports=metric_reports,
            query_level_results=query_results
        )

        self._print_summary(report)
        return report

    def _calculate_statistics(self, scores: list[float]) -> MetricStatistics:
        n = len(scores)
        c_below = sum(1 for s in scores if s < 0.5)
        c_above = sum(1 for s in scores if s > 0.7)
        return MetricStatistics(
            mean=statistics.mean(scores),
            std_dev=statistics.stdev(scores) if n > 1 else 0.0,
            min=min(scores),
            max=max(scores),
            median=statistics.median(scores),
            count_below_50=c_below,
            percent_below_50=round(c_below / n * 100, 2),
            count_above_70=c_above,
            percent_above_70=round(c_above / n * 100, 2)
        )

    def _create_query_level_results(self, examples, all_scores) -> list[QueryLevelResult]:
        results = []
        for i, ex in enumerate(examples):
            m_scores = {name: scores[i] for name, scores in all_scores.items()}
            results.append(QueryLevelResult(
                query_index=i,
                query=ex.query,
                metric_scores=m_scores,
                overall_score=sum(m_scores.values()) / len(m_scores)
            ))
        return results

    def _print_summary(self, report: EvaluationReport):
        table = Table(title="Resumen de Evaluación NSCA", show_header=True, header_style="bold magenta")
        table.add_column("Métrica")
        table.add_column("Promedio", justify="right")
        table.add_column("Min", justify="right")
        table.add_column("Max", justify="right")
        table.add_column("> 0.7 (Bien)", justify="right", style="green")

        for mr in report.metric_reports:
            table.add_row(
                mr.metric_name,
                f"{mr.statistics.mean:.3f}",
                f"{mr.statistics.min:.3f}",
                f"{mr.statistics.max:.3f}",
                f"{mr.statistics.count_above_70} ({mr.statistics.percent_above_70}%)"
            )
        console.print(table)