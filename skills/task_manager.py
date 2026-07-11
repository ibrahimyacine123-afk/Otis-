from .db import get_supabase_client
from .utils import parse_date_to_iso

class TaskManager:
    def __init__(self):
        self.db = get_supabase_client()

    def add_task(self, title: str, description: str = None, due_date: str = None, priority: str = "medium", milestone_name: str = None) -> dict:
        """Ajoute une nouvelle tâche dans la base de données."""
        data = {
            "title": title,
            "status": "todo",
            "priority": priority
        }
        if description:
            data["description"] = description
        if due_date:
            parsed_date = parse_date_to_iso(due_date)
            if parsed_date:
                data["due_date"] = parsed_date
            else:
                return {"success": False, "error": f"Format de date non reconnu : {due_date}"}
            
        try:
            if milestone_name:
                # Récupère l'id du milestone ou le crée s'il n'existe pas
                ms_res = self.create_milestone(milestone_name)
                if ms_res.get("success") and "id" in ms_res.get("data", [{}])[0]:
                    data["milestone_id"] = ms_res["data"][0]["id"]
                    
            response = self.db.table("tasks").insert(data).execute()
            return {"success": True, "data": response.data}
        except Exception as e:
            print(f"Erreur lors de l'ajout de la tâche : {e}")
            return {"success": False, "error": str(e)}

    def create_milestone(self, name: str, description: str = None) -> dict:
        """Crée un nouveau jalon ou retourne celui existant."""
        try:
            # Vérifier s'il existe
            existing = self.db.table("milestones").select("*").eq("name", name).execute()
            if existing.data:
                return {"success": True, "data": existing.data}
                
            # Sinon on le crée
            data = {"name": name}
            if description:
                data["description"] = description
            response = self.db.table("milestones").insert(data).execute()
            return {"success": True, "data": response.data}
        except Exception as e:
            print(f"Erreur lors de la gestion du jalon : {e}")
            return {"success": False, "error": str(e)}

    def list_ongoing_tasks(self) -> list:
        """Récupère toutes les tâches non terminées (todo, in_progress, backlog)."""
        try:
            response = self.db.table("tasks").select("*").in_("status", ["todo", "in_progress", "backlog"]).order("created_at", desc=True).execute()
            return response.data
        except Exception as e:
            print(f"Erreur lors de la récupération des tâches : {e}")
            return []
