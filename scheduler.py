import os
import sys

# Voir server.py pour le detail : force l'UTF-8 pour eviter un UnicodeEncodeError
# sur les emojis quand stdout n'est pas un terminal interactif (ex: log redirige,
# ce qui est le cas normal pour un scheduler lance en arriere-plan).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import requests
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from skills.trinity import TrinityFilter
from skills.task_manager import TaskManager

load_dotenv()

BRIDGE_SEND_URL = os.environ.get("BRIDGE_SEND_URL", "http://127.0.0.1:8002/send")
# Premier numero de la liste ALLOWED_NUMBERS (server.py / whatsapp-bridge/index.js) par defaut.
OWNER_NUMBER = os.environ.get("OTIS_OWNER_NUMBER", "905411078112")


def build_morning_message() -> str:
    trinity = TrinityFilter()
    task_manager = TaskManager()

    principle = trinity.get_daily_principle()
    summary = task_manager.get_daily_summary()

    lines = ["🌅 *Rituel matinal OTIS*"]

    if principle:
        lines.append(f"\n💡 Principe du jour ({principle.get('source')}) : *{principle.get('principle_name')}*")
        lines.append(principle.get("principle_text", ""))
    else:
        lines.append("\n💡 Pas de principe de sagesse disponible aujourd'hui (table wisdom_principles vide ou inaccessible).")

    due_today = summary.get("due_today", []) if summary.get("success") else []
    overdue = summary.get("overdue", []) if summary.get("success") else []

    if due_today:
        lines.append(f"\n📋 Tâches du jour ({len(due_today)}) :")
        for t in due_today[:5]:
            lines.append(f"- {t.get('title')}")
    else:
        lines.append("\n📋 Aucune tâche due aujourd'hui.")

    if overdue:
        lines.append(f"\n⚠️ {len(overdue)} tâche(s) en retard à rattraper.")

    lines.append("\nQuelle est ta priorité N°1 aujourd'hui — exacte, chiffrée, datée ?")

    return "\n".join(lines)


def send_morning_ritual():
    message = build_morning_message()
    try:
        r = requests.post(BRIDGE_SEND_URL, json={"to": OWNER_NUMBER, "message": message}, timeout=15)
        print(f"[Rituel matinal] Envoi -> {r.status_code} {r.text}")
    except Exception as e:
        print(f"[Rituel matinal] Erreur d'envoi vers le pont WhatsApp (bridge lance ? port {BRIDGE_SEND_URL}) : {e}")


if __name__ == "__main__":
    scheduler = BlockingScheduler(timezone="Europe/Istanbul")
    scheduler.add_job(send_morning_ritual, CronTrigger(hour=7, minute=0, timezone="Europe/Istanbul"), id="rituel_matinal")
    print("⏰ Scheduler OTIS actif — rituel matinal programmé à 07:00 Europe/Istanbul.")
    print("   (Nécessite que whatsapp-bridge/index.js tourne pour l'envoi effectif sur WhatsApp.)")
    scheduler.start()
