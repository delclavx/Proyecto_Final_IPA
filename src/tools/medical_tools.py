import os
import sqlite3
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.tools import tool
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