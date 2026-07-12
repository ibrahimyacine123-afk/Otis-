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

    def get_daily_summary(self) -> dict:
        """Résumé du jour (inspiré Leantime/Plane) : tâches dues aujourd'hui + en cours + en retard."""
        from datetime import datetime, timezone, timedelta
        try:
            now = datetime.now(timezone.utc)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            today_end = (now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)).isoformat()

            due_today = self.db.table("tasks").select("*").gte("due_date", today_start).lt("due_date", today_end).in_("status", ["todo", "in_progress", "backlog"]).execute().data
            overdue = self.db.table("tasks").select("*").lt("due_date", today_start).in_("status", ["todo", "in_progress", "backlog"]).execute().data
            in_progress = self.db.table("tasks").select("*").eq("status", "in_progress").execute().data

            return {
                "success": True,
                "due_today": due_today,
                "overdue": overdue,
                "in_progress": in_progress
            }
        except Exception as e:
            print(f"Erreur lors du résumé du jour : {e}")
            return {"success": False, "due_today": [], "overdue": [], "in_progress": [], "error": str(e)}
