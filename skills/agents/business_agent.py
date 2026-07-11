import json
from .base_agent import BaseAgent
from connectors.mpc_base import BusinessConnector

class BusinessAgent(BaseAgent):
    def __init__(self):
        system_prompt = """Ton rôle est de gérer toutes les opérations de support client, CRM et communication business de l'agence d'assistance IA (comme HubSpot ou HubSpot+SendGrid).
Tu as la capacité d'envoyer des e-mails de suivi aux clients, d'enregistrer de nouveaux prospects (leads) et de mettre à jour les statuts dans le CRM.
Sois toujours courtois, professionnel et synthétique dans tes retours."""
        
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "send_email",
                    "description": "Envoie un e-mail professionnel ou un e-mail de suivi à un client/prospect.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "to_email": {"type": "string", "description": "L'adresse e-mail du destinataire."},
                            "subject": {"type": "string", "description": "Sujet de l'e-mail."},
                            "body": {"type": "string", "description": "Contenu complet de l'e-mail."}
                        },
                        "required": ["to_email", "subject", "body"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "register_lead",
                    "description": "Enregistre un nouveau prospect (lead) dans le CRM de l'entreprise.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Nom complet du prospect."},
                            "company": {"type": "string", "description": "Nom de l'entreprise du prospect."},
                            "email": {"type": "string", "description": "Adresse e-mail de contact."}
                        },
                        "required": ["name", "company", "email"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_crm",
                    "description": "Met à jour le statut d'un lead existant dans le CRM (ex: contacté, intéressé, client, perdu).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lead_id": {"type": "string", "description": "L'identifiant du lead."},
                            "status": {"type": "string", "description": "Le nouveau statut du lead.", "enum": ["new", "contacted", "interested", "qualified", "closed_won", "closed_lost"]}
                        },
                        "required": ["lead_id", "status"]
                    }
                }
            }
        ]
        super().__init__("BusinessAgent", "l'Assistant Business et CRM d'OTIS", system_prompt, tools)
        self.business_connector = BusinessConnector()

    def execute_tool(self, name: str, args: dict) -> str:
        try:
            if name == "send_email":
                res = self.business_connector.send_followup_email(
                    args.get("to_email"), args.get("subject"), args.get("body")
                )
                return json.dumps(res)
            elif name == "register_lead":
                res = self.business_connector.register_lead(
                    args.get("name"), args.get("company"), args.get("email")
                )
                return json.dumps(res)
            elif name == "update_crm":
                res = self.business_connector.update_crm_lead(
                    args.get("lead_id"), args.get("status")
                )
                return json.dumps(res)
            else:
                return json.dumps({"error": f"Outil inconnu : {name}"})
        except Exception as e:
            return json.dumps({"error": str(e)})
