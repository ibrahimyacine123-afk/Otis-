import json
from typing import Dict, Any

class BusinessConnector:
    """
    Connecteur d'intégration générique pour les automatisations d'entreprise (CRM, E-mails, Leads).
    Sert de passerelle pour les futures intégrations (HubSpot, SendGrid, Salesforce, etc.).
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)
        
    def send_followup_email(self, to_email: str, subject: str, body: str) -> Dict[str, Any]:
        """
        Simule l'envoi d'un e-mail de suivi via un service tiers (ex: SendGrid, Resend).
        """
        if not self.enabled:
            return {"success": False, "error": "Le connecteur business est désactivé."}
            
        print(f"      [✉️ Email] Envoi en cours à {to_email} - Sujet: {subject}")
        return {
            "success": True,
            "connector": "SendGrid_Simulated",
            "action": "send_email",
            "to": to_email,
            "subject": subject,
            "status": "delivered"
        }
        
    def update_crm_lead(self, lead_id: str, status: str) -> Dict[str, Any]:
        """
        Simule la mise à jour du statut d'un prospect dans le CRM (ex: HubSpot, Salesforce).
        """
        if not self.enabled:
            return {"success": False, "error": "Le connecteur business est désactivé."}
            
        print(f"      [📊 CRM] Mise à jour du lead {lead_id} -> Statut: {status}")
        return {
            "success": True,
            "connector": "HubSpot_Simulated",
            "action": "update_lead",
            "lead_id": lead_id,
            "new_status": status,
            "status": "updated"
        }
        
    def register_lead(self, name: str, company: str, email: str) -> Dict[str, Any]:
        """
        Simule la création d'un nouveau lead dans le CRM d'entreprise.
        """
        if not self.enabled:
            return {"success": False, "error": "Le connecteur business est désactivé."}
            
        print(f"      [👥 CRM] Nouveau lead enregistré : {name} ({company})")
        return {
            "success": True,
            "connector": "HubSpot_Simulated",
            "action": "create_lead",
            "lead_data": {
                "name": name,
                "company": company,
                "email": email
            },
            "status": "created"
        }
