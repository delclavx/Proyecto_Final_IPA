from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langfuse.langchain import CallbackHandler
from langchain_core.messages import SystemMessage, ToolMessage, AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

from agents.state import AgentState
from agents.prompts import SYSTEM_PROMPT
from tools.medical_tools import consultar_protocolos_nsca, obtener_metricas_atleta
from agents.sql_agent import SQLAnalystAgent

from config import settings

# --- CONFIGURACIÓN ---
langfuse_handler = CallbackHandler()

llm = ChatGroq(
    model=settings.groq_model_name, 
    temperature=0, 
    callbacks=[langfuse_handler]
)

tools = [consultar_protocolos_nsca, obtener_metricas_atleta] 
llm_with_tools = llm.bind_tools(tools)

sql_analyst_node = SQLAnalystAgent()

# --- NODOS ---

def router_entry_node(state: AgentState):
    """Nodo neutral de entrada para decidir el camino sin generar texto previo."""
    return state

def call_model(state: AgentState, config: RunnableConfig):
    """Nodo Orquestador (Cerebro)."""
    messages = state['messages']
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    
    response = llm_with_tools.invoke(messages, config=config)
    return {"messages": [response]}

def execute_tools(state: AgentState, config: RunnableConfig):
    """Nodo para herramientas RAG."""
    messages = state['messages']
    last_message = messages[-1]
    tool_responses = []
    
    for tool_call in last_message.tool_calls:
        if tool_call['name'] == "obtener_metricas_atleta":
            result = obtener_metricas_atleta.invoke(tool_call['args'], config=config)
        elif tool_call['name'] == "consultar_protocolos_nsca":
            result = consultar_protocolos_nsca.invoke(tool_call['args'], config=config)
        
        tool_responses.append(ToolMessage(
            tool_call_id=tool_call['id'],
            content=str(result)
        ))
    return {"messages": tool_responses}

# --- LÓGICA DE RUTEO ---

def should_continue(state: AgentState):
    messages = state['messages']
    last_message = messages[-1]

    # 1. Si el LLM generó una llamada a herramientas (RAG)
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "herramientas"

    # 2. Si el mensaje es del Humano y pide datos, vamos directo al SQL
    if isinstance(last_message, HumanMessage):
        content = last_message.content.lower()
        sql_keywords = ["media", "enero", "febrero", "promedio", "atleta", "sueño", "rpe"]
        if any(w in content for w in sql_keywords):
            return "sql_analyst"

    # 3. Por defecto, si es charla normal o ya terminó el proceso, END
    return END

# --- CONSTRUCCIÓN DEL GRAFO ---
builder = StateGraph(AgentState)

builder.add_node("router", router_entry_node)
builder.add_node("agente", call_model)
builder.add_node("herramientas", execute_tools)
builder.add_node("sql_analyst", sql_analyst_node)

# EL PUNTO DE ENTRADA ES EL ROUTER
builder.set_entry_point("router")

# Ruteo inicial desde el Router
builder.add_conditional_edges(
    "router",
    should_continue,
    {
        "herramientas": "agente",      # Si detecta intención RAG, al agente para que use tools
        "sql_analyst": "sql_analyst",  # SI ES SQL, VA DIRECTO (Evita que el agente hable antes)
        END: "agente"                  # Charla normal
    }
)

# Ruteo de seguimiento desde el Agente
builder.add_conditional_edges(
    "agente",
    should_continue,
    {
        "herramientas": "herramientas",
        "sql_analyst": "sql_analyst",
        END: END
    }
)

# Bordes de retorno y cierre
builder.add_edge("herramientas", "agente")
builder.add_edge("sql_analyst", END) # CONVERGENCIA: El SQL responde y termina.

graph = builder.compile()