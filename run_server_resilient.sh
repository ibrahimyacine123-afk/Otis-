#!/bin/bash
# Wrapper resilient pour server.py (FastAPI) : redemarre automatiquement en cas
# de crash. Cf. BLOCKERS.md "chantier process manager" -- server.py a ete trouve
# arrete a plusieurs reprises entre deux sessions sans qu'aucun crash ne soit
# visible dans les logs (probablement tue avec le process parent qui l'avait lance
# en tache de fond, pas un vrai crash applicatif).
#
# Usage : ./run_server_resilient.sh   (a lancer depuis la racine du projet)
cd "$(dirname "$0")"

while true; do
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Demarrage de server.py..."
    ./venv/Scripts/python.exe -m uvicorn server:app --host 127.0.0.1 --port 8000
    EXIT_CODE=$?
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] server.py arrete (code $EXIT_CODE). Redemarrage dans 3s..."
    sleep 3
done
