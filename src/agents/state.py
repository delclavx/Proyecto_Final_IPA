from typing import TypedDict, Annotated, List, Union
import operator
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    # El historial de chat se va acumulando (operator.add)
    messages: Annotated[List[BaseMessage], operator.add]
    # Guardamos el ID del atleta para mantener el contexto
    atleta_id: str
    # Lista de riesgos que el agente va detectando durante el flujo
    riesgos_detectados: List[str]