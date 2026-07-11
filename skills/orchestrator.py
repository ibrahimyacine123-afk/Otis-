import os
import json
from openai import OpenAI
from dotenv import load_dotenv

from .thought_logger import ThoughtLogger
from .agents.business_agent import BusinessAgent
from .agents.productivity_agent import ProductivityAgent
from .web_search import WebSearcher

load_dotenv()

class MPCOrchestrator:
    def __init__(self):
        nvidia_api_key = os.environ.get("NVIDIA_API_KEY")
        if not nvidia_api_key:
            raise ValueError("NVIDIA_API_KEY manquante.")
            
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=nvidia_api_key
        )
        self.model = "meta/llama-3.3-70b-instruct"
        
        self.business_agent = BusinessAgent()
        self.productivity_agent = ProductivityAgent()
        self.thought_logger = ThoughtLogger()
        self.web_searcher = WebSearcher()
        
        self.system_prompt = """Tu es OTIS (CEO Agent), l'orchestrateur principal du système.
        Tu gères une équipe de sous-agents experts (BusinessAgent et ProductivityAgent).
        Tu as également accès directement à la mémoire de l'utilisateur (Memory) pour logguer des pensées.
        
        Processus de réflexion (ReAct) :
        1. Analyse la demande globale.
        2. Décompose la demande et délègue les tâches commerciales, CRM et de support au BusinessAgent et les tâches de projet au ProductivityAgent en utilisant les outils appropriés.
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

    def process_request(self, user_input: str) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        max_iterations = 6
        for iteration in range(max_iterations):
            response = self.client.chat.completions.create(
                model=self.model,
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
