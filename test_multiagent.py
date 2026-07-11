import sys
from skills.orchestrator import MPCOrchestrator

print("🚀 Initialisation du test automatisé...")
try:
    orchestrator = MPCOrchestrator()
    prompt = "Ajoute une tâche 'Préparer le rapport financier' dans mon milestone actuel, et bloque-moi un rendez-vous demain à 10h pour bosser dessus."
    print(f"Demande utilisateur : {prompt}\n")
    print("[OTIS réfléchit...]\n")
    
    response = orchestrator.process_request(prompt)
    print(f"\n🤖 Réponse finale : {response}")
except Exception as e:
    print(f"Erreur : {e}")
