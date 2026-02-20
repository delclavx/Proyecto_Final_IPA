from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langfuse.callback import CallbackHandler
from langchain_core.messages import SystemMessage
from langchain_core.messages import ToolMessage
from agents.state import AgentState
from agents.prompts import SYSTEM_PROMPT
from tools.medical_tools import consultar_protocolos_nsca, obtener_metricas_atleta

# Configura el callback con tus credenciales (asegúrate de que están en el .env)
langfuse_handler = CallbackHandler()

# 1. Configuración del "Cerebro"
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0, callbacks=[langfuse_handler])
tools = [consultar_protocolos_nsca, obtener_metricas_atleta]
llm_with_tools = llm.bind_tools(tools)

# 2. Nodo de Inteligencia: El Analista
def call_model(state: AgentState):
    """Nodo principal que razona usando el System Prompt y las herramientas."""
    messages = state['messages']
    
    # Si es el primer mensaje, inyectamos las reglas de la NSCA
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

# 3. Nodo de Acción: El Bibliotecario/Ejecutor
def execute_tools(state: AgentState):
    """Nodo que ejecuta las herramientas y devuelve los resultados al historial."""
    messages = state['messages'] # Definimos la variable messages desde el estado
    last_message = messages[-1]
    
    # Lista para guardar las respuestas de las herramientas
    tool_responses = []
    
    for tool_call in last_message.tool_calls:
        # Ejecución de la herramienta
        if tool_call['name'] == "obtener_metricas_atleta":
            result = obtener_metricas_atleta.invoke(tool_call['args'])
        elif tool_call['name'] == "consultar_protocolos_nsca":
            result = consultar_protocolos_nsca.invoke(tool_call['args'])
        
        # Creamos el mensaje de respuesta de la herramienta
        tool_responses.append(ToolMessage(
            tool_call_id=tool_call['id'],
            content=str(result)
        ))
    
    return {"messages": tool_responses}

# --- CONSTRUCCIÓN DEL GRAFO ---
builder = StateGraph(AgentState)

builder.add_node("agente", call_model)
builder.add_node("herramientas", execute_tools)

builder.set_entry_point("agente")

# Lógica condicional: ¿Seguimos hablando o necesitamos usar una herramienta?
def should_continue(state: AgentState):
    last_message = state['messages'][-1]
    if last_message.tool_calls:
        return "herramientas"
    return END

builder.add_conditional_edges("agente", should_continue)
builder.add_edge("herramientas", "agente")

graph = builder.compile()