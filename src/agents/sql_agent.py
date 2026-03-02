import os
import re
from langchain_community.utilities import SQLDatabase
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from agents.state import AgentState
from langchain_core.messages import SystemMessage, ToolMessage, HumanMessage, AIMessage

class SQLAnalystAgent:
    def __init__(self):
        # Configuración de ruta
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        db_path = os.path.join(base_dir, "src", "database", "kinetic_guard.db")
        self.db = SQLDatabase.from_uri(f"sqlite:///{db_path}")
        self.llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)

    def __call__(self, state: AgentState):
        # 1. Extraer mensajes y definir last_message
        messages = state.get("messages", [])
        
        # Filtramos para obtener el contenido del último mensaje del humano
        human_messages = [
            m.content for m in messages 
            if isinstance(m, HumanMessage) or (isinstance(m, tuple) and m[0] == "human")
        ]
        last_message = human_messages[-1] if human_messages else ""
        
        # 2. Obtener el esquema y definir la variable schema
        # (Aquí es donde fallaba antes por no estar definida)
        db_schema = self.db.get_table_info()

        sql_gen_prompt = ChatPromptTemplate.from_template(
            "Eres un experto en SQLite. Genera ÚNICAMENTE código SQL puro.\n"
            "Esquema: {schema}\n"
            "Pregunta: {question}\n\n"
            "REGLAS OBLIGATORIAS:\n"
            "1. NO incluyas texto explicativo.\n"
            "2. NO uses funciones que no existen en SQLite como STDDEV.\n"
            "3. Atleta 1 = 'atleta_01'.\n"
            "4. Devuelve el código SQL seco, sin bloques de markdown.\n"
            "5. Redondea resultados: ROUND(columna, 2)."
        )
        
        try:
            # Generación de la Query
            sql_chain = sql_gen_prompt | self.llm | StrOutputParser()
            # Usamos db_schema que acabamos de definir
            raw_query = sql_chain.invoke({"schema": db_schema, "question": last_message})
            
            # Limpieza de la Query
            start_index = raw_query.upper().find("SELECT")
            if start_index == -1:
                return {"messages": [AIMessage(content="No se encontraron datos específicos para procesar.")]}
            
            clean_query = raw_query[start_index:].strip()
            clean_query = clean_query.replace("```", "").split(';')[0].strip()
            
            # Ejecución
            db_results = self.db.run(clean_query)
            
            # 3. REDACCIÓN FINAL
            response_prompt = ChatPromptTemplate.from_template(
                "Eres el Asistente de Rendimiento NSCA. Datos: {results}\n"
                "Pregunta: {question}\n\n"
                "INSTRUCCIONES:\n"
                "- Responde de forma profesional.\n"
                "- Si el promedio de sueño < 7h, advierte del riesgo.\n"
                "- NO hagas preguntas al usuario al terminar."
            )
            
            final_answer = (response_prompt | self.llm | StrOutputParser()).invoke({
                "results": db_results, 
                "question": last_message
            })

            return {"messages": [AIMessage(content=final_answer)]}

        except Exception as e:
            # Mensaje de error controlado para no romper el flujo
            return {"messages": [AIMessage(content=f"Nota: No se pudieron extraer métricas de la base de datos: {str(e)}")]}