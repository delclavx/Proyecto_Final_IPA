import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from agents.main_graph import graph

load_dotenv()

def run_performance_assistant():
    print("--- Asistente de Rendimiento NSCA ---")
    print("(Escribe 'q' para salir)")
    
    # ID de sesión para mantener la memoria de la conversación
    config = {"configurable": {"thread_id": "sesion_entrenador_01"}}
    
    while True:
        user_input = input("\nEntrenador: ")
        if user_input.lower() in ["exit", "quit", "q"]:
            print("Cerrando asistente...")
            break

        # Filtramos el stream para capturar solo los cambios en el nodo 'agente'
        # Esto evita que se impriman los fragmentos de los PDFs (RAG) en la consola
        for event in graph.stream(
            {"messages": [HumanMessage(content=user_input)], "atleta_id": "atleta_01"},
            config,
            stream_mode="updates" # Cambiado a 'updates' para detectar nodos específicos
        ):
            if "agente" in event:
                # Extraemos el último mensaje generado por el cerebro del agente
                last_message = event["agente"]["messages"][-1]
                
                # Solo imprimimos si tiene contenido y NO es una llamada a herramientas
                if last_message.content and not last_message.tool_calls:
                    print(f"\nAsistente: {last_message.content}")

if __name__ == "__main__":
    run_performance_assistant()