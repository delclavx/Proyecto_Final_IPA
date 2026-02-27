"""LangFuse observability client."""

import os

from langfuse import get_client

from src.config import settings
from langfuse import Langfuse



def configure_langfuse():
    """
    Configure LangFuse by setting environment variables for @observe decorators.

    In v3, the SDK reads from environment variables automatically.
    Call this at the start of scripts that use @observe decorators.
    """
    os.environ["LANGFUSE_PUBLIC_KEY"] = settings.langfuse_public_key
    os.environ["LANGFUSE_SECRET_KEY"] = settings.langfuse_secret_key
    os.environ["LANGFUSE_HOST"] = settings.langfuse_base_url


def flush_langfuse():
    """
    Flush LangFuse traces to ensure all data is sent.

    Call this before exiting your application to prevent losing traces.
    LangFuse batches traces asynchronously for performance, so without
    flushing, recent traces might not be sent.

    Example:
        from src.observability.langfuse_client import flush_langfuse

        rag_pipeline.query("What is RAG?")
        flush_langfuse()  # Ensure trace is sent before script exits
    """
    get_client().flush()

def get_langfuse_instance():
    """Devuelve una instancia del cliente de Langfuse configurada."""
    return Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_base_url
    )