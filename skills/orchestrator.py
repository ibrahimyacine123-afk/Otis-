import json
from dotenv import load_dotenv

from .thought_logger import ThoughtLogger
from .agents.business_agent import BusinessAgent
from .agents.productivity_agent import ProductivityAgent
from .web_search import WebSearcher
from .trinity import TrinityFilter
from .llm_client import get_llm_client, get_llm_model, chat_completion_with_fallback

load_dotenv()

# Registre des agents (inspiré crewAI/AutoGPT) : décrit les capacités de chaque
# sous-agent pour que l'orchestrateur route ses délégations de façon informée,
# sans changer le mécanisme de tool-calling existant.
AGENT_REGISTRY = [
    {
        "name": "BusinessAgent",
        "delegate_tool": "delegate_to_business",
        "capabilities": ["send_email", "register_lead", "update_crm"],
        "description": "Support client, CRM, communication business (e-mails, leads)."
    },
    {
        "name": "ProductivityAgent",
        "delegate_tool": "delegate_to_productivity",
        "capabilities": ["add_task", "list_tasks", "create_milestone", "schedule_meeting", "daily_summary", "log_transaction", "get_account_balance", "get_monthly_finance_summary"],
        "description": "Tâches, jalons, calendrier et finances personnelles (comptes, dépenses, revenus)."
    }
]


def _render_agent_registry() -> str:
    lines = []
    for agent in AGENT_REGISTRY:
        lines.append(f"- {agent['name']} ({agent['delegate_tool']}) : {agent['description']} Capacités : {', '.join(agent['capabilities'])}.")
    return "\n".join(lines)


class MPCOrchestrator:
    def __init__(self):
        self.client = get_llm_client()
        self.model = get_llm_model()

        self.business_agent = BusinessAgent()
        self.productivity_agent = ProductivityAgent()
        self.thought_logger = ThoughtLogger()
        self.web_searcher = WebSearcher()
        self.trinity = TrinityFilter()

        self.system_prompt = f"""Tu es OTIS — mentor-stratège d'Aurel, fusion de trois sagesses :
- Holiday (stoïcien) : tu détectes l'ego, tu poses la question dure. "Qui décide — l'ego ou la sagesse ?"
- Hill (visionnaire) : tu exiges des désirs EXACTS (montant, date, méthode). Tu refuses le vague.
- Goleman (cœur) : tu nommes l'émotion présente, tu la traites comme une donnée intelligente, jamais comme un ordre.
Ton ton : direct, chaleureux, concis (format WhatsApp : 2-6 phrases). Tu questionnes plus que tu n'ordonnes. Tu célèbres les victoires sans complaisance. Tu n'abandonnes jamais, tu ne flattes jamais.
Face à une décision à enjeu : 1) nomme l'émotion 2) teste l'ego 3) exige l'exactitude 4) puis seulement conseille.

Tu es également l'orchestrateur technique (CEO Agent) du système. Tu gères une équipe de sous-agents experts
et tu as accès direct à la mémoire de l'utilisateur (Memory) pour logguer des pensées.

Registre des agents disponibles :
{_render_agent_registry()}

Processus de réflexion (ReAct) :
1. Analyse la demande globale. Si un contexte Trinity (ego/clarté/foi/émotion) t'est fourni, tiens-en compte dans ton ton et tes questions.
2. Décompose la demande et délègue les tâches commerciales, CRM et de support au BusinessAgent et les tâches de projet/finances au ProductivityAgent en utilisant les outils appropriés.
3. Observe les retours de tes agents. S'ils échouent, essaie de reformuler.
4. Synthétise les retours de tous tes agents dans une réponse finale claire et naturelle pour l'utilisateur.
"""

        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "delegate_to_business",
                    "description": "Délègue une tâche liée au support client, CRM ou communication business (e-mails, leads) au conseiller business.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "prompt": {"type": "string", "description": "L'instruction détaillée pour l'agent business."}
                        },
                        "required": ["prompt"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "delegate_to_productivity",
                    "description": "Délègue une tâche liée à l'organisation, aux jalons ou à la to-do list au Chef de Projet.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "prompt": {"type": "string", "description": "L'instruction détaillée pour l'agent de productivité."}
                        },
                        "required": ["prompt"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "add_thought",
                    "description": "Enregistre une note rapide, une pensée ou un journal dans la mémoire centrale.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string"},
                            "category": {"type": "string"}
                        },
                        "required": ["content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_web",
                    "description": "Effectue une recherche sur le web (DuckDuckGo) pour trouver des informations récentes, des actualités ou des faits en temps réel.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "La requête de recherche (ex: cours de l'action Nvidia, météo à Paris)"}
                        },
                        "required": ["query"]
                    }
                }
            }
        ]

    def _execute_tool(self, name: str, args: dict) -> str:
        try:
            if name == "delegate_to_business":
                print(f"      [📞 Transfert] Appel du BusinessAgent avec: {args.get('prompt')}")
                return self.business_agent.run(args.get('prompt'))
                
            elif name == "delegate_to_productivity":
                print(f"      [📞 Transfert] Appel du ProductivityAgent avec: {args.get('prompt')}")
                return self.productivity_agent.run(args.get('prompt'))
                
            elif name == "add_thought":
                res = self.thought_logger.add_thought(
                    args.get("content"), args.get("category", "general")
                )
                return json.dumps(res)
                
            elif name == "search_web":
                print(f"      [🔍 Recherche Web] Requête : {args.get('query')}")
                res = self.web_searcher.search(args.get("query"))
                return json.dumps(res)
                
            else:
                return json.dumps({"error": f"Outil inconnu : {name}"})
                
        except Exception as e:
            return json.dumps({"error": str(e)})

    def _clarify_via_trinity(self, user_input: str, scores: dict) -> str:
        """Génère une réponse de clarification courte (persona OTIS) quand l'ego domine
        et que le désir manque de clarté, au lieu d'exécuter la demande."""
        prompt = f"""L'utilisateur a écrit : "{user_input}"

Le filtre Trinity a détecté : ego_test_score={scores.get('ego_test_score')}/10 (élevé = motivé par l'ego),
desire_clarity_score={scores.get('desire_clarity_score')}/10 (bas = désir vague), émotion dominante :
{scores.get('emotion_identified')} (intensité {scores.get('emotion_score')}/10).

En restant OTIS (ton direct, chaleureux, 2-6 phrases, format WhatsApp), NE PAS exécuter la demande.
Nomme l'émotion perçue, questionne doucement la motivation (ego vs sagesse), puis exige un désir exact
(montant/date/méthode précis) avant d'aller plus loin."""

        try:
            completion = chat_completion_with_fallback(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=300
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Avant d'aller plus loin : qu'est-ce qui te pousse vraiment vers ça, et quel est le montant/la date/la méthode exacte ? ({e})"

    def process_request(self, user_input: str) -> str:
        trinity_context = ""
        trinity_scores = self.trinity.evaluate(user_input)

        if trinity_scores["is_high_stakes"]:
            self.trinity.log_decision(
                agent_id="Orchestrator",
                decision_name=user_input,
                decision_context={"user_input": user_input},
                scores=trinity_scores
            )

            if self.trinity.needs_clarification(trinity_scores):
                return self._clarify_via_trinity(user_input, trinity_scores)

            trinity_context = (
                f"\n\n[Contexte Trinity — ne pas exposer tel quel à l'utilisateur] "
                f"ego={trinity_scores['ego_test_score']}/10, "
                f"clarté={trinity_scores['desire_clarity_score']}/10, "
                f"foi={trinity_scores['faith_score']}/10, "
                f"émotion={trinity_scores['emotion_identified']} "
                f"({trinity_scores['emotion_score']}/10)."
            )

        messages = [
            {"role": "system", "content": self.system_prompt + trinity_context},
            {"role": "user", "content": user_input}
        ]

        max_iterations = 6
        for iteration in range(max_iterations):
            response = chat_completion_with_fallback(
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
                temperature=0.2
            )
            
            message = response.choices[0].message
            messages.append(message)
            
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    print(f"\n   [👑 CEO Thought] J'ordonne l'action : {tool_call.function.name}")
                    args = json.loads(tool_call.function.arguments)
                    observation = self._execute_tool(tool_call.function.name, args)
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": observation
                    })
            else:
                return message.content

        return "Je suis désolé, je n'ai pas pu terminer la coordination après plusieurs tentatives."
