import json
from dotenv import load_dotenv

from .db import get_supabase_client
from .llm_client import get_llm_client, get_llm_model, chat_completion_with_fallback

load_dotenv()

TRINITY_PROMPT = """Tu es le filtre de sagesse Trinity d'OTIS. Analyse UNIQUEMENT le message utilisateur
ci-dessous et reponds avec un objet JSON strict, sans phrase d'introduction, sans conclusion,
sans formatage Markdown.

Determine d'abord si la demande est a ENJEU (argent, engagement, decision strategique ou
relationnelle importante) ou TRIVIALE (question factuelle simple, salutation, demande d'info
sans consequence : ex "quelle heure est-il", "salut").

Si TRIVIALE : is_high_stakes=false, tous les scores a 0, emotion="neutre".

Si A ENJEU, evalue selon 3 tests :
- HOLIDAY (ego) : la demande est-elle motivee par l'ego (vouloir impressionner, prouver, agir
  vite par orgueil) ou par la sagesse (methode, patience) ? Score 1-10 ou 10 = ego maximal.
- HILL (clarte + foi) : le desir exprime est-il EXACT (montant precis, date precise, methode
  precise) ? desire_clarity_score 1-10 (10 = parfaitement exact). L'utilisateur semble-t-il
  croire reellement au resultat ? faith_score 1-10 (10 = conviction totale).
- GOLEMAN (emotion) : quelle emotion domine le message (peur, avidite, excitation, colere,
  confiance, calme...) ? emotion_score 1-10 ou 1-3 = emotion reactive/impulsive et 7-10 =
  emotion intelligente/maitrisee.

Structure JSON attendue :
{
  "is_high_stakes": true|false,
  "ego_test_score": 0-10,
  "desire_clarity_score": 0-10,
  "faith_score": 0-10,
  "emotion_identified": "nom de l'emotion",
  "emotion_score": 0-10
}"""


class TrinityFilter:
    """Filtre de sagesse OTIS : evalue chaque demande a enjeu via 3 tests
    (Holiday/ego, Hill/clarte-foi, Goleman/emotion) en UN SEUL appel LLM,
    journalise le resultat dans decision_audit, et signale les demandes
    ou l'ego domine sans clarte du desir."""

    def __init__(self):
        self.client = get_llm_client()
        self.model = get_llm_model()
        self.db = get_supabase_client()

    def evaluate(self, user_input: str) -> dict:
        """Fait l'UNIQUE appel LLM qui classifie l'enjeu ET note les 3 tests Trinity."""
        default = {
            "is_high_stakes": False,
            "ego_test_score": 0,
            "desire_clarity_score": 0,
            "faith_score": 0,
            "emotion_identified": "neutre",
            "emotion_score": 0
        }
        try:
            completion = chat_completion_with_fallback(
                messages=[
                    {"role": "system", "content": TRINITY_PROMPT},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.1,
                max_tokens=300
            )
            raw = completion.choices[0].message.content.strip()
            if raw.startswith("```json"):
                raw = raw[7:]
            if raw.startswith("```"):
                raw = raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            result = json.loads(raw.strip())

            return {
                "is_high_stakes": bool(result.get("is_high_stakes", False)),
                "ego_test_score": int(result.get("ego_test_score", 0) or 0),
                "desire_clarity_score": int(result.get("desire_clarity_score", 0) or 0),
                "faith_score": int(result.get("faith_score", 0) or 0),
                "emotion_identified": result.get("emotion_identified", "neutre"),
                "emotion_score": int(result.get("emotion_score", 0) or 0)
            }
        except Exception as e:
            print(f"[Trinity] Erreur d'evaluation, filtre desactive pour cette requete : {e}")
            return default

    def log_decision(self, agent_id: str, decision_name: str, decision_context: dict, scores: dict) -> dict:
        """Journalise la decision evaluee dans decision_audit via la fonction SQL dediee."""
        try:
            response = self.db.rpc("log_decision_with_trinity", {
                "p_agent_id": agent_id,
                "p_decision_name": decision_name[:500],
                "p_decision_context": decision_context,
                "p_ego_test_score": scores.get("ego_test_score") or None,
                "p_desire_clarity_score": scores.get("desire_clarity_score") or None,
                "p_faith_score": scores.get("faith_score") or None,
                "p_emotion_identified": scores.get("emotion_identified"),
                "p_emotion_score": scores.get("emotion_score") or None
            }).execute()
            return {"success": True, "data": response.data}
        except Exception as e:
            print(f"[Trinity] Erreur de journalisation dans decision_audit : {e}")
            return {"success": False, "error": str(e)}

    def get_daily_principle(self) -> dict:
        """Retourne un principe de sagesse (rotation par priorite puis date de creation)."""
        try:
            response = self.db.table("wisdom_principles").select("*").order("priority", desc=True).order("created_at", desc=False).execute()
            principles = response.data
            if not principles:
                return None
            from datetime import date
            index = date.today().toordinal() % len(principles)
            return principles[index]
        except Exception as e:
            print(f"[Trinity] Erreur de recuperation du principe du jour : {e}")
            return None

    def needs_clarification(self, scores: dict) -> bool:
        return scores.get("ego_test_score", 0) >= 8 and scores.get("desire_clarity_score", 10) <= 4
