import os
from openai import OpenAI

DEFAULT_MODEL = "meta/llama-3.3-70b-instruct"

_client = None


def get_llm_client() -> OpenAI:
    """Client NVIDIA (compatible OpenAI) partagé par tout OTIS.
    Factorise les instanciations dupliquées (orchestrator, base_agent, trinity)."""
    global _client
    if _client is None:
        nvidia_api_key = os.environ.get("NVIDIA_API_KEY")
        if not nvidia_api_key:
            raise ValueError("NVIDIA_API_KEY manquante.")
        _client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=nvidia_api_key
        )
    return _client


def get_llm_model() -> str:
    return os.environ.get("NVIDIA_MODEL", DEFAULT_MODEL)
