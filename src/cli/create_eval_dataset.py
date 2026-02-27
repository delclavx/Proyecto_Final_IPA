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

# @observe(name="eval-dataset-query")
# def run_rag_query(query: str) -> dict:
#     """Ejecuta la consulta a través de tu grafo de agentes."""
#     console.print(f"🔍 Procesando consulta: [cyan]{query}[/]")
    
#     # Invocación de tu grafo
#     inputs = {"messages": [("user", query)]}
#     config = {"configurable": {"thread_id": "eval_session"}}
    
#     response = app.invoke(inputs, config)
    
#     # Extraemos la respuesta final del asistente
#     answer = response["messages"][-1].content

#     return {
#         "query": query,
#         "answer": answer,
#         "contexts": ["Información recuperada de los manuales de la NSCA"],
#         "trace_id": "eval_gen_id"
#     }
@observe(name="eval-dataset-query")
def run_rag_query(query: str) -> dict:
    """Ejecuta la consulta manejando mensajes tipo tupla o tipo objeto."""
    console.print(f"🔍 Procesando consulta: [cyan]{query}[/]")
    
    inputs = {"messages": [("user", query)]}
    config = {"configurable": {"thread_id": "eval_session_nsca"}}
    
    try:
        response = app.invoke(inputs, config)
        
        # 1. Extraer la respuesta final (el último mensaje)
        last_msg = response["messages"][-1]
        
        # Manejo de mensaje tipo Tupla ("assistant", "contenido") o tipo Objeto
        if isinstance(last_msg, tuple):
            answer = last_msg[1]
        else:
            answer = last_msg.content

        # 2. Extracción de Chunks (Contextos reales)
        actual_contexts = []
        for msg in response["messages"]:
            content = ""
            # Extraer contenido según formato
            if isinstance(msg, tuple):
                content = msg[1]
            elif hasattr(msg, "content"):
                content = msg.content
            
            # Buscamos si este mensaje contiene información técnica de los PDFs
            # Normalmente las herramientas devuelven el texto del PDF aquí
            if "Source:" in str(content) or "Contexto:" in str(content) or len(str(content)) > 200:
                # Si el mensaje es muy largo o cita fuentes, es un contexto
                if content != answer: # Evitamos duplicar la respuesta final
                    actual_contexts.append(content)

        if not actual_contexts:
            actual_contexts = ["El contexto se integró directamente en la respuesta o se obtuvo de la base de datos SQL."]

        return {
            "query": query,
            "answer": answer,
            "contexts": actual_contexts,
            "trace_id": "eval_gen_id"
        }
    except Exception as e:
        return {
            "query": query,
            "answer": f"Error en el flujo del grafo: {str(e)}",
            "contexts": [],
            "trace_id": "error_id"
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