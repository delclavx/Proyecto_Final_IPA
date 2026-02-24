import os
import sqlite3
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.tools import tool
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

# --- HERRAMIENTA 1: CONSULTA RAG (Conocimiento Científico) ---
@tool
def consultar_protocolos_nsca(query: str):
    """Consulta los manuales de la NSCA para obtener protocolos de recuperación, 
    prevención de lesiones y estándares de entrenamiento."""
    embeddings = AzureOpenAIEmbeddings(
        azure_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"),
        openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION")
    )
    # Buscamos en la carpeta que ya tienes creada
    vector_db = Chroma(persist_directory="src/vector_store", embedding_function=embeddings)
    docs = vector_db.similarity_search(query, k=3)
    return "\n\n".join([d.page_content for d in docs])

# --- HERRAMIENTA 2: CONSULTA SQL (Datos del Atleta) ---
@tool
def obtener_metricas_atleta(atleta_id: str):
    """Obtiene los últimos 7 días de carga de entrenamiento, sueño y fatiga (RPE) de un atleta."""
    import os
    
    # 1. Asegurar la ruta correcta a la DB desde cualquier carpeta
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "database", "kinetic_guard.db")
    
    # 2. Limpiar el ID (por si acaso el LLM manda "Atleta_01" con mayúscula)
    atleta_id_clean = atleta_id.lower().strip()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT fecha, carga_entrenamiento, hrv_ms, horas_sueno, rpe_fatiga 
            FROM daily_metrics 
            WHERE LOWER(atleta_id) = ? 
            ORDER BY fecha DESC LIMIT 7
        ''', (atleta_id_clean,))
        rows = cursor.fetchall()
    finally:
        conn.close()
    
    if not rows:
        return f"Error: No hay datos en SQL para el ID '{atleta_id_clean}'. Revisa setup_sql.py."
    
    return f"Datos reales del atleta encontrados: {rows}"

# --- HERRAMIENTA 3: CONSULTA SQL DINÁMICA (Text-to-SQL) ---
@tool
def consultar_sql_dinamico(query: str):
    """Consulta la base de datos de manera dinámica usando lenguaje natural para generar y ejecutar consultas SQL seguras."""
    # Ruta a la base de datos
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "database", "kinetic_guard.db")
    
    # Conectar a la base de datos
    db = SQLDatabase.from_uri(f"sqlite:///{db_path}")
    
    # Configurar el LLM para generar SQL
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    
    # Prompt para generar SQL
    sql_prompt = PromptTemplate.from_template(
        "Dado el esquema de la base de datos:\n{schema}\n\nGenera una consulta SQL para responder: {question}\nSolo devuelve la consulta SQL, sin explicaciones."
    )
    
    # Cadena para generar SQL
    chain = sql_prompt | llm | StrOutputParser()
    
    # Obtener esquema de la tabla
    schema = db.get_table_info()
    
    # Generar la consulta SQL
    try:
        sql_query = chain.invoke({"schema": schema, "question": query}).strip()
        # Limpiar posibles backticks o texto extra
        if sql_query.startswith("```sql"):
            sql_query = sql_query[6:]
        if sql_query.endswith("```"):
            sql_query = sql_query[:-3]
        sql_query = sql_query.strip()
        
        # Ejecutar la consulta
        result = db.run(sql_query)
        return f"Consulta SQL generada: {sql_query}\n\nResultados: {result}"
    except Exception as e:
        return f"Error al generar o ejecutar la consulta: {str(e)}"