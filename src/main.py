import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from agents.main_graph import graph, langfuse_handler

load_dotenv()

def run_performance_assistant():
    print("--- Asistente de Rendimiento NSCA ---")
    print("(Escribe 'q' para salir)")
    
    # ID de sesión y callbacks para que toda la ejecución (grafo + herramientas) sea una sola traza en LangFuse
    config = {
        "configurable": {"thread_id": "sesion_entrenador_01"},
        "callbacks": [langfuse_handler],
    }
    
    while True:
        user_input = input("\nEntrenador: ")
        if user_input.lower() in ["exit", "quit", "q"]:
            print("Cerrando asistente...")
            break

# ... (resto del código igual)
        for event in graph.stream(
            {"messages": [HumanMessage(content=user_input)], "atleta_id": "atleta_01"},
            config,
            stream_mode="updates"
        ):
            # Escuchamos tanto al 'agente' como al 'sql_analyst'
            node_name = "agente" if "agente" in event else "sql_analyst" if "sql_analyst" in event else None
            
            if node_name:
                # Extraemos el mensaje (el SQL Analyst devuelve una lista de mensajes en tu __call__)
                last_message = event[node_name]["messages"][-1]
                
                # Manejamos si el mensaje es un objeto AIMessage o un string
                content = getattr(last_message, 'content', last_message[1] if isinstance(last_message, tuple) else "")
                
                # Solo imprimimos si hay contenido y NO estamos en medio de una llamada a herramientas
                if content and not getattr(last_message, 'tool_calls', None):
                    print(f"\nAsistente: {content}")

if __name__ == "__main__":
    run_performance_assistant()