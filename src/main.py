import os
import uuid
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from agents.main_graph import graph, langfuse_handler

load_dotenv()

def run_performance_assistant():
    print("--- Asistente de Rendimiento NSCA ---")
    print("(Escribe 'q' para salir)")
    
    session_id = str(uuid.uuid4())
    config = {
        "configurable": {"thread_id": session_id},
        "callbacks": [langfuse_handler],
    }
    
    while True:
        user_input = input("\nEntrenador: ")
        if user_input.lower() in ["exit", "quit", "q"]:
            print("Cerrando asistente...")
            break

        # Procesamos el stream
        for event in graph.stream(
            {"messages": [HumanMessage(content=user_input)], "atleta_id": "atleta_01"},
            config,
            stream_mode="updates"
        ):
            for node_name, data in event.items():
                if "messages" in data:
                    last_message = data["messages"][-1]
                    
                    content = ""
                    is_assistant = False

                    # Extracción de contenido
                    if isinstance(last_message, AIMessage):
                        content = last_message.content
                        is_assistant = True
                    elif isinstance(last_message, tuple) and last_message[0] == "assistant":
                        content = last_message[1]
                        is_assistant = True
                    
                    # FILTRO UNIFICADO
                    if is_assistant and content.strip() and not getattr(last_message, 'tool_calls', None):
                        # Filtro anti-saludos protocolarios
                        saludos_prohibidos = ["hola!", "ayudarte hoy", "ayudarte con tu entrenamiento", "¿en qué puedo ayudarte"]
                        if not any(s in content.lower() for s in saludos_prohibidos):
                            print(f"\nAsistente: {content}")
                
if __name__ == "__main__":
    run_performance_assistant()