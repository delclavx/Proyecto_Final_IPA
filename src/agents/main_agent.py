from langgraph.graph import StateGraph, END
from tools.medical_tools import consultar_protocolos_nsca, obtener_metricas_atleta

# 1. Definir el nodo que analiza los datos del SQL
def analizar_biometria(state):
    # Aquí se usaría tu herramienta obtener_metricas_atleta
    pass

# 2. Definir el nodo que consulta la ciencia (RAG)
def consultar_ciencia(state):
    # Aquí se usaría tu herramienta consultar_protocolos_nsca
    pass

# 3. Construir el grafo
workflow = StateGraph(AgentState)
workflow.add_node("analista_biometrico", analizar_biometria)
workflow.add_node("consultor_nsca", consultar_ciencia)

# El Estudiante 2 conectará estos nodos con flechas lógicas