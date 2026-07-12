import sys
import os

# Force l'UTF-8 sur stdout/stderr : sous Windows, dès que la sortie n'est pas un
# terminal interactif (log redirigé, service, etc.), Python utilise le codepage
# système (ex: cp1254) qui ne supporte pas les emojis utilisés dans les logs —
# ce qui fait planter chaque requête avec UnicodeEncodeError -> 500.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from skills.orchestrator import MPCOrchestrator
from skills.utils import format_for_whatsapp

app = FastAPI(title="OTIS API")
orchestrator = MPCOrchestrator()

# Vos numéros WhatsApp autorisés (sans le +)
ALLOWED_NUMBERS = ["905411078112", "905442846826", "62225754636356"]

class MessagePayload(BaseModel):
    message: str
    sender: str

@app.post("/webhook")
async def webhook(payload: MessagePayload):
    print(f"📥 Message reçu de {payload.sender} : {payload.message}")
    
    # Vérification de sécurité
    if payload.sender not in ALLOWED_NUMBERS:
        print(f"⚠️ Rejeté : Numéro non autorisé ({payload.sender})")
        raise HTTPException(status_code=403, detail="Numéro non autorisé.")
        
    try:
        response = orchestrator.process_request(payload.message)
        formatted_response = format_for_whatsapp(response)
        print(f"📤 Réponse générée : {formatted_response}")
        return {"success": True, "response": formatted_response}
    except Exception as e:
        print(f"Erreur lors du traitement : {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🚀 Démarrage de l'API OTIS sur le port 8000...")
    print(f"🔒 Numéros autorisés : {', '.join(ALLOWED_NUMBERS)}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
