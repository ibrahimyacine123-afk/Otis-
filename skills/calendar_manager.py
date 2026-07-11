from .db import get_supabase_client
from .utils import parse_date_to_iso

class CalendarManager:
    def __init__(self):
        self.db = get_supabase_client()

    def schedule_meeting(self, title: str, start_time: str) -> dict:
        """Ajoute un événement ou rendez-vous dans la table des rappels/calendrier."""
        parsed_time = parse_date_to_iso(start_time)
        if not parsed_time:
            return {"success": False, "error": f"Format de date non reconnu pour le rendez-vous : {start_time}"}
            
        data = {
            "message": title,
            "trigger_at": parsed_time,
            "channel": "calendar"
        }
        try:
            response = self.db.table("reminders").insert(data).execute()
            return {"success": True, "data": response.data}
        except Exception as e:
            print(f"Erreur lors de l'ajout au calendrier : {e}")
            return {"success": False, "error": str(e)}
