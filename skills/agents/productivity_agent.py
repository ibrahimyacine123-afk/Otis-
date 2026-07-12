import json
from .base_agent import BaseAgent
from ..task_manager import TaskManager
from ..calendar_manager import CalendarManager
from ..finance_tracker import FinanceTracker

class ProductivityAgent(BaseAgent):
    def __init__(self):
        system_prompt = """Ton rôle est de gérer la productivité, les tâches et les finances personnelles de l'utilisateur
comme un Chef de Projet (façon Leantime/Plane) doublé d'un gestionnaire de comptes (façon Firefly III).
Tu dois structurer les tâches de l'utilisateur, gérer ses transactions financières par compte, et lui fournir
des résumés clairs (tâches du jour, solde, résumé mensuel). Tu as la capacité de créer des jalons (milestones)
pour regrouper les tâches si nécessaire."""
        
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
            },
            {
                "type": "function",
                "function": {
                    "name": "daily_summary",
                    "description": "Retourne le résumé du jour : tâches dues aujourd'hui, tâches en retard, tâches en cours."
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "log_transaction",
                    "description": "Enregistre une dépense ou un revenu sur un compte donné.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "amount": {"type": "number", "description": "Montant de la transaction"},
                            "description": {"type": "string"},
                            "transaction_type": {"type": "string", "enum": ["income", "expense"]},
                            "category": {"type": "string", "description": "Catégorie de la transaction (ex: restaurant, salaire)"},
                            "account": {"type": "string", "description": "Nom du compte (défaut: Principal)"}
                        },
                        "required": ["amount", "description", "transaction_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_account_balance",
                    "description": "Retourne le solde d'un compte précis.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "account": {"type": "string", "description": "Nom du compte (défaut: Principal)"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_monthly_finance_summary",
                    "description": "Retourne le résumé financier du mois courant (revenus, dépenses, solde, répartition par catégorie)."
                }
            }
        ]
        super().__init__("ProductivityAgent", "le Chef de Projet et Gestionnaire de Temps d'OTIS", system_prompt, tools)
        self.task_manager = TaskManager()
        self.calendar_manager = CalendarManager()
        self.finance_tracker = FinanceTracker()

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
            elif name == "daily_summary":
                res = self.task_manager.get_daily_summary()
                return json.dumps(res)
            elif name == "log_transaction":
                res = self.finance_tracker.add_transaction(
                    args.get("amount"), args.get("description"),
                    args.get("transaction_type"), args.get("category", "general"),
                    args.get("account", "Principal")
                )
                return json.dumps(res)
            elif name == "get_account_balance":
                res = self.finance_tracker.get_account_balance(args.get("account", "Principal"))
                return json.dumps(res)
            elif name == "get_monthly_finance_summary":
                res = self.finance_tracker.get_monthly_summary()
                return json.dumps(res)
            else:
                return json.dumps({"error": f"Outil inconnu : {name}"})
        except Exception as e:
            return json.dumps({"error": str(e)})
