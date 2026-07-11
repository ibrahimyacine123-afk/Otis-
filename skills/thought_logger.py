from .db import get_supabase_client

class ThoughtLogger:
    def __init__(self):
        self.db = get_supabase_client()

    def add_thought(self, content: str, category: str = "general") -> dict:
        """Enregistre une pensée, une note à la volée ou une entrée de journal."""
        data = {
            "content": content,
            "category": category
        }
        try:
            response = self.db.table("thoughts").insert(data).execute()
            return {"success": True, "data": response.data}
        except Exception as e:
            print(f"Erreur lors de l'enregistrement de la pensée : {e}")
            return {"success": False, "error": str(e)}
