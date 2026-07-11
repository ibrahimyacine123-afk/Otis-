import json
from .base_agent import BaseAgent
from ..task_manager import TaskManager
from ..calendar_manager import CalendarManager

class ProductivityAgent(BaseAgent):
    def __init__(self):
        system_prompt = """Ton rôle est de gérer la productivité et les tâches de l'utilisateur comme un Chef de Projet (façon Leantime/Plane).
Tu dois structurer les tâches de l'utilisateur. Tu as la capacité de créer des jalons (milestones) pour regrouper les tâches si nécessaire."""
        
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "add_task",
                    "description": "Ajoute une nouvelle tâche à la to-do list.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "due_date": {"type": "string"},
                            "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]},
                            "milestone_name": {"type": "string", "description": "Nom du jalon/projet optionnel"}
                        },
                        "required": ["title"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_tasks",
                    "description": "Récupère la liste des tâches non terminées."
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_milestone",
                    "description": "Crée un nouveau jalon (milestone) pour regrouper des tâches.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"}
                        },
                        "required": ["name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "schedule_meeting",
                    "description": "Bloque un rendez-vous ou ajoute un événement au calendrier.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "Sujet du rendez-vous"},
                            "start_time": {"type": "string", "description": "Date et heure (ex: demain à 10h)"}
                        },
                        "required": ["title", "start_time"]
                    }
                }
            }
        ]
        super().__init__("ProductivityAgent", "le Chef de Projet et Gestionnaire de Temps d'OTIS", system_prompt, tools)
        self.task_manager = TaskManager()
        self.calendar_manager = CalendarManager()

    def execute_tool(self, name: str, args: dict) -> str:
        try:
            if name == "add_task":
                res = self.task_manager.add_task(
                    args.get("title"), args.get("description"), 
                    args.get("due_date"), args.get("priority", "medium"),
                    args.get("milestone_name")
                )
                return json.dumps(res)
            elif name == "list_tasks":
                res = self.task_manager.list_ongoing_tasks()
                return json.dumps(res)
            elif name == "create_milestone":
                res = self.task_manager.create_milestone(
                    args.get("name"), args.get("description")
                )
                return json.dumps(res)
            elif name == "schedule_meeting":
                res = self.calendar_manager.schedule_meeting(
                    args.get("title"), args.get("start_time")
                )
                return json.dumps(res)
            else:
                return json.dumps({"error": f"Outil inconnu : {name}"})
        except Exception as e:
            return json.dumps({"error": str(e)})
