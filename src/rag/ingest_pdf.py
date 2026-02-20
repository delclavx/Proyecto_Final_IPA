import os
import re
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv

load_dotenv()

def limpiar_texto_nsca(texto):
    """Limpia ruido específico de los PDFs de la NSCA."""
    # 1. Eliminar pies de página con URLs y nombres de revistas
    texto = re.sub(r'Strength and Conditioning Journal\s*\|\s*www\.nsca-scj\.com', '', texto)
    # 2. Eliminar avisos de Copyright repetitivos detectados en las páginas
    texto = re.sub(r'Copyright National Strength and Conditioning Association.*', '', texto)
    # 3. Eliminar números de página aislados (ej: "1", "2", etc. al final/inicio de página)
    texto = re.sub(r'^\s*\d+\s*$', '', texto, flags=re.MULTILINE)
    # 4. Eliminar menciones a reproducciones no autorizadas
    texto = texto.replace("Unauthorized reproduction of this article is prohibited.", "")
    # 5. Normalizar espacios en blanco múltiples
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def run_ingestion():
    data_path = "src/data/"
    vector_db_path = "src/vector_store"
    
    documents = []
    if not os.path.exists(data_path):
        os.makedirs(data_path)
        print(f"Creada carpeta {data_path}. Añade tus PDFs ahí.")
        return

    for file in os.listdir(data_path):
        if file.endswith(".pdf"):
            print(f"📄 Procesando: {file}...")
            loader = PyPDFLoader(os.path.join(data_path, file))
            # Cargamos y aplicamos limpieza a cada página
            page_docs = loader.load()
            for doc in page_docs:
                doc.page_content = limpiar_texto_nsca(doc.page_content)
            documents.extend(page_docs)

    if not documents:
        print("❌ No se encontraron PDFs en src/data/")
        return

    # Chunking con los parámetros de tu .env
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=int(os.getenv("INGESTION_CHUNK_SIZE", 1000)),
        chunk_overlap=int(os.getenv("INGESTION_CHUNK_OVERLAP", 200))
    )
    chunks = text_splitter.split_documents(documents)
    print(f"✂️ Documentos limpios y divididos en {len(chunks)} fragmentos.")

    embeddings = AzureOpenAIEmbeddings(
        azure_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"),
        openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION")
    )

    print("Wait... Creando memoria científica en base de datos vectorial...")
    vector_db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=vector_db_path
    )
    
    print(f"✅ ÉXITO: Memoria científica limpia creada en {vector_db_path}")

if __name__ == "__main__":
    run_ingestion()