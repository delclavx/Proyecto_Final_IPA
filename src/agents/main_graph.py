from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langfuse.langchain import CallbackHandler
from langchain_core.messages import SystemMessage, ToolMessage, AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from agents.state import AgentState

from agents.state import AgentState
from agents.prompts import SYSTEM_PROMPT
from tools.medical_tools import consultar_protocolos_nsca
from agents.sql_agent import SQLAnalystAgent

from config import settings

# --- CONFIGURACIÓN ---
langfuse_handler = CallbackHandler()

llm = ChatGroq(
    model=settings.groq_model_name, 
    temperature=0, 
    callbacks=[langfuse_handler]
)

# Herramientas exclusivas para el agente orquestador
tools = [consultar_protocolos_nsca] 
llm_with_tools = llm.bind_tools(tools)

sql_analyst_node = SQLAnalystAgent()

# --- NODOS ---

def router_entry_node(state: AgentState):
    """Punto de entrada neutral para decidir la ruta sin respuestas previas."""
    return state

def call_model(state: AgentState, config: RunnableConfig):
    """Nodo Orquestador (Agente 1: Experto en Protocolos)."""
    messages = state['messages']
    
    # Inyectamos el System Prompt si es una sesión nueva
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    
    response = llm_with_tools.invoke(messages, config=config)
    return {"messages": [response]}

def execute_tools(state: AgentState, config: RunnableConfig):
    """Nodo de ejecución para herramientas RAG."""
    messages = state['messages']
    last_message = messages[-1]
    tool_responses = []
    
    for tool_call in last_message.tool_calls:
        # Solo procesamos la herramienta RAG, el SQL ya tiene su propio agente
        if tool_call['name'] == "consultar_protocolos_nsca":
            result = consultar_protocolos_nsca.invoke(tool_call['args'], config=config)
        
            tool_responses.append(ToolMessage(
                tool_call_id=tool_call['id'],
                content=str(result)
            ))
    return {"messages": tool_responses}

def should_continue(state: AgentState):
    messages = state['messages']
    last_message = messages[-1]

    # 1. Ejecución de herramientas RAG
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "herramientas"

    user_message = next((m for m in reversed(messages) if isinstance(m, HumanMessage)), None)
    
    if user_message:
        content = user_message.content.lower()
        
        urgency_keywords = ["qué puede ser", "dolor", "orina", "té", "gripe", "lesión", "nsca", "protocolo"]
        sql_keywords = ["media", "promedio", "cuánto", "registros", "atleta 1", "atleta_01", "esta semana"]
        
        has_urgency = any(w in content for w in urgency_keywords)
        has_sql = any(w in content for w in sql_keywords)
        # Comprobamos si ya tenemos una respuesta del analista SQL
        already_has_sql_res = any("resultado de SQL" in m.content for m in messages if isinstance(m, AIMessage))

        # --- LÓGICA DE FLUJO ---
        
        # Si es el primer paso y hay urgencia, vamos al Agente Principal
        if has_urgency and last_message == user_message:
            return "agente"
        
        # Si ya pasó por el agente (o no había urgencia) y falta el SQL, vamos al SQL
        if has_sql and not already_has_sql_res:
            return "sql_analyst"

    return END

# --- CONSTRUCCIÓN DEL GRAFO ---
builder = StateGraph(AgentState)

builder.add_node("router", router_entry_node)
builder.add_node("agente", call_model)
builder.add_node("herramientas", execute_tools)
builder.add_node("sql_analyst", sql_analyst_node)

builder.set_entry_point("router")

# Mapeo del Router: Decide el primer paso
builder.add_conditional_edges(
    "router",
    should_continue,
    {
        "herramientas": "agente",
        "sql_analyst": "sql_analyst",
        "agente": "agente",
        END: "agente" 
    }
)

# Mapeo del Agente: Decide si terminar o ir al SQL
builder.add_conditional_edges(
    "agente", 
    should_continue,
    {
        "herramientas": "herramientas",
        "sql_analyst": "sql_analyst", # <--- Clave para la transición Agente 1 -> Agente 2
        END: END
    }
)

builder.add_edge("herramientas", "agente")
builder.add_edge("sql_analyst", END)

graph = builder.compile()