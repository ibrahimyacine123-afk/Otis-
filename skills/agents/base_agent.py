import json
from ..llm_client import get_llm_client, get_llm_model, chat_completion_with_fallback

class BaseAgent:
    def __init__(self, name: str, role: str, system_prompt: str, tools: list):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.tools = tools

        self.client = get_llm_client()
        self.model = get_llm_model()

    def execute_tool(self, name: str, args: dict) -> str:
        """Méthode à surcharger dans chaque agent spécifique."""
        raise NotImplementedError("execute_tool n'est pas implémenté pour cet agent.")

    def run(self, user_input: str) -> str:
        """Boucle ReAct spécifique à l'agent."""
        messages = [
            {"role": "system", "content": f"Tu es {self.name}, {self.role}.\n{self.system_prompt}"},
            {"role": "user", "content": user_input}
        ]
        
        for iteration in range(5):
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
                    print(f"\n   [{self.name} - Thought] Utilisation de l'outil : {tool_call.function.name}")
                    args = json.loads(tool_call.function.arguments)
                    observation = self.execute_tool(tool_call.function.name, args)
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": observation
                    })
            else:
                return message.content
        return "Erreur : Limite d'itérations atteinte pour cet agent."
