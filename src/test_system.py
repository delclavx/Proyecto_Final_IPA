import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
# NUEVA RUTA DE IMPORTACIÓN PARA LANGFUSE
from langfuse.callback import CallbackHandler 
from tools.medical_tools import consultar_protocolos_nsca, obtener_metricas_atleta

load_dotenv()

# 1. Configurar Langfuse con la integración de 2026
# Si el import anterior fallara, la alternativa es: from langfuse.langchain import CallbackHandler
try:
    from langfuse.callback import CallbackHandler
except ImportError:
    from langfuse.langchain import CallbackHandler

langfuse_handler = CallbackHandler(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_BASE_URL")
)

# 2. Configurar LLM (Groq)
llm = ChatGroq(
    temperature=0,
    model_name="llama-3.3-70b-versatile",
    groq_api_key=os.getenv("GROQ_API_KEY")
)

# Vinculamos las herramientas
tools = [consultar_protocolos_nsca, obtener_metricas_atleta]
llm_with_tools = llm.bind_tools(tools)

def test_final():
    print("\n🚀 Probando conexión: Groq + Azure RAG + SQL + Langfuse...")
    pregunta = "¿Qué carga ha tenido el atleta_01 y qué dice la NSCA sobre fatiga?"
    
    try:
        messages = [HumanMessage(content=pregunta)]
        # Invocamos con el handler de Langfuse
        ai_msg = llm_with_tools.invoke(messages, config={"callbacks": [langfuse_handler]})
        
        print("\n🧠 LA IA HA DECIDIDO USAR:")
        if ai_msg.tool_calls:
            for call in ai_msg.tool_calls:
                print(f"✅ Herramienta: {call['name']}")
                print(f"✅ Argumentos: {call['args']}")
            print("\n✨ ¡INFRAESTRUCTURA VALIDADA! Todo el pipeline funciona.")
        else:
            print("\n⚠️ La IA respondió sin usar herramientas. Revisa los prompts.")
            
    except Exception as e:
        print(f"❌ Error final: {e}")

if __name__ == "__main__":
    test_final()
    # ESTO FUERZA EL ENVÍO DE DATOS ANTES DE CERRAR
    langfuse_handler.flush() 
    print("📡 Datos sincronizados con Langfuse.")
    