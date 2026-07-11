import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_supabase_client = None

def get_supabase_client() -> Client:
    """Retourne une instance unique du client Supabase."""
    global _supabase_client
    if _supabase_client is None:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("Les variables SUPABASE_URL et SUPABASE_KEY doivent être définies.")
        _supabase_client = create_client(url, key)
    return _supabase_client
