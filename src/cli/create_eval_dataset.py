import argparse
import json
import random
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console

# 1. Configuración de rutas para encontrar 'src'
root_path = Path(__file__).resolve().parent.parent
sys.path.append(str(root_path))

# 2. Carga de entorno y parche de Langfuse
load_dotenv()
console = Console()

try:
    from langfuse.decorators import observe
except ImportError:
    def observe(name=None):
        return lambda f: f

# 3. Importar tu Grafo Real
from src.agents.main_graph import graph as app

@observe(name="eval-dataset-query")
def run_rag_query(query: str) -> dict:
    """Ejecuta la consulta a través de tu grafo de agentes."""
    console.print(f"🔍 Procesando consulta: [cyan]{query}[/]")
    
    # Invocación de tu grafo
    inputs = {"messages": [("user", query)]}
    config = {"configurable": {"thread_id": "eval_session"}}
    
    response = app.invoke(inputs, config)
    
    # Extraemos la respuesta final del asistente
    answer = response["messages"][-1].content

    return {
        "query": query,
        "answer": answer,
        "contexts": ["Información recuperada de los manuales de la NSCA"],
        "trace_id": "eval_gen_id"
    }

def load_queries(queries_file: Path) -> list:
    with open(queries_file, "r", encoding='utf-8') as f:
        data = json.load(f)
    # Soporta tanto lista directa como objeto con llave "queries"
    return data["queries"] if isinstance(data, dict) else data

def main() -> None:
    parser = argparse.ArgumentParser(description="Generador de Dataset de Evaluación NSCA")
    parser.add_argument("--num-questions", "-n", type=int, default=None)
    parser.add_argument("--queries-file", type=str, default="Evaluations/my_queries.json")
    parser.add_argument("--output-file", type=str, default="Evaluations/eval_dataset.json")
    args = parser.parse_args()

    queries_file = Path(args.queries_file)
    output_file = Path(args.output_file)

    # Cargar y filtrar preguntas
    queries = load_queries(queries_file)
    if args.num_questions:
        queries = random.sample(queries, min(args.num_questions, len(queries)))

    console.print(f"[bold blue]🚀 Iniciando evaluación de {len(queries)} preguntas...[/]")

    evaluation_examples = []
    for query in queries:
        try:
            result = run_rag_query(query)
            evaluation_examples.append(result)
        except Exception as e:
            console.print(f"[red]❌ Error en query '{query}': {e}[/]")

    # Guardar resultados
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding='utf-8') as f:
        json.dump(evaluation_examples, f, indent=4, ensure_ascii=False)

    console.print(f"[bold green]✅ Dataset guardado en {output_file}[/]")

if __name__ == "__main__":
    main()