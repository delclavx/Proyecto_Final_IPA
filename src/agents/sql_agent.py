import os
import re
from langchain_community.utilities import SQLDatabase
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from agents.state import AgentState

class SQLAnalystAgent:
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        db_path = os.path.join(base_dir, "src", "database", "kinetic_guard.db")
        self.db = SQLDatabase.from_uri(f"sqlite:///{db_path}")
        self.llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)

    def __call__(self, state: AgentState):
        last_message = state["messages"][-1].content
        schema = self.db.get_table_info()

        # 1. Generador de Query (SQLite)
        sql_gen_prompt = ChatPromptTemplate.from_template(
            "Eres un experto en SQLite. Tabla: 'daily_metrics'. Esquema:\n{schema}\n\n"
            "Pregunta: {question}\n\n"
            "REGLAS:\n"
            "- Atleta 1 = 'atleta_01'.\n"
            "- Enero = strftime('%m', fecha) = '01'.\n"
            "- Genera SOLO SQL puro."
        )
        
        try:
            sql_chain = sql_gen_prompt | self.llm | StrOutputParser()
            raw_query = sql_chain.invoke({"schema": schema, "question": last_message})
            clean_query = re.sub(r'```sql|```', '', raw_query).strip()
            
            # Ejecución
            db_results = self.db.run(clean_query)
            
            # 2. REDACCIÓN FINAL (Para evitar que el orquestador dude)
            response_prompt = ChatPromptTemplate.from_template(
                "Eres el Asistente de Rendimiento NSCA. Basándote en este resultado de SQL: {results}\n"
                "Responde a la pregunta: {question}\n\n"
                "REGLA NSCA: El mínimo de sueño son 7h. Si el dato es {results}, indica si cumple o no."
            )
            
            final_answer = (response_prompt | self.llm | StrOutputParser()).invoke({
                "results": db_results, 
                "question": last_message
            })

            return {"messages": [("assistant", final_answer)]}

        except Exception as e:
            return {"messages": [("assistant", f"Error en análisis: {str(e)}")]}