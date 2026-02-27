# Proyecto Final IPA

Asistente de rendimiento basado en NSCA con RAG (ChromaDB) y base de datos SQLite para métricas de atletas.

## Setup

1. **Configuración de entorno**  
   Copia `.env.example` a `.env` y rellena las variables (Groq, Azure OpenAI, Langfuse).

2. **Crear ChromaDB (memoria científica)**  
   Coloca tus PDFs en `src/data/` y ejecuta la ingesta para generar el índice vectorial:

   ```bash
   uv run python src/rag/ingest_pdf.py
   ```

   El índice se guarda en `src/vector_store`.

3. **Crear base de datos SQL (métricas de atletas)**  
   Genera la base SQLite con datos de ejemplo:

   ```bash
   uv run python src/database/setup_sql.py
   ```

   Se crea `src/database/kinetic_guard.db`.

4. **Ejecutar la aplicación**  
   Desde la raíz del proyecto:

   ```bash
   cd src && uv run python main.py
   ```

   Escribe `q` o `exit` para salir del asistente.

5. **Create evaluation dataset**  
   Desde la raíz del proyecto:

   ```bash
   PYTHONPATH=.:src uv run python src/cli/create_eval_dataset.py \
    --queries-file Evaluations/my_queries.json \
    --output-file Evaluations/eval_dataset.json \
    -n 7
   ```

6. **Evaluate**  
   Desde la raíz del proyecto:

   ```bash
   uv run python -m src.cli.evaluate
   ```


## Requisitos

- Python ≥ 3.11  
- Dependencias gestionadas con `uv` (ver `pyproject.toml`)


#Dime cuando ha dormido de media en enero el atleta 1?