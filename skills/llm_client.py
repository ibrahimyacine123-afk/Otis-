import os
import queue
import threading
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DEFAULT_MODEL = "meta/llama-3.3-70b-instruct"
FALLBACK_MODEL = os.environ.get("NVIDIA_FALLBACK_MODEL", "meta/llama-3.1-70b-instruct")
PRIMARY_TIMEOUT_SECONDS = 30

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


def _call_model(model: str, **kwargs):
    client = get_llm_client()
    return client.chat.completions.create(model=model, **kwargs)


def chat_completion_with_fallback(messages, tools=None, tool_choice=None, temperature=0.2, max_tokens=None):
    """Appelle le modèle primaire (NVIDIA_MODEL / meta/llama-3.3-70b-instruct par défaut).
    S'il ne répond pas dans les PRIMARY_TIMEOUT_SECONDS (30s), bascule automatiquement
    sur FALLBACK_MODEL (meta/llama-3.1-70b-instruct par défaut, même API NVIDIA) et
    journalise le basculement. Les erreurs immédiates (pas un timeout) ne déclenchent
    PAS de fallback et remontent telles quelles.

    Implémentation en thread démon + Queue (plutôt que ThreadPoolExecutor) : un appel
    qui reste bloqué sur le réseau (constaté en conditions réelles sur l'API NVIDIA,
    voir BLOCKERS.md) ne peut pas être annulé côté Python, mais un thread démon ne
    bloque pas la sortie du process — contrairement à ThreadPoolExecutor, dont les
    workers sont rejoints automatiquement à la fermeture (atexit) et auraient fait
    hang tout le programme en attendant un appel qui ne reviendra jamais."""
    primary_model = get_llm_model()

    kwargs = {"temperature": temperature}
    if tools is not None:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = tool_choice or "auto"
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens

    result_queue = queue.Queue(maxsize=1)

    def _worker():
        try:
            result_queue.put(("ok", _call_model(primary_model, messages=messages, **kwargs)))
        except Exception as e:
            result_queue.put(("error", e))

    threading.Thread(target=_worker, daemon=True, name="otis-llm-primary").start()

    try:
        status, payload = result_queue.get(timeout=PRIMARY_TIMEOUT_SECONDS)
        if status == "error":
            raise payload
        return payload
    except queue.Empty:
        print(f"[llm_client] ⏱️ Timeout de {PRIMARY_TIMEOUT_SECONDS}s sur '{primary_model}' -> fallback sur '{FALLBACK_MODEL}'")
        return _call_model(FALLBACK_MODEL, messages=messages, **kwargs)
