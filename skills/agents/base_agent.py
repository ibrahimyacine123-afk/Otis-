import os
import json
from openai import OpenAI

class BaseAgent:
    def __init__(self, name: str, role: str, system_prompt: str, tools: list):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.tools = tools
        
        nvidia_api_key = os.environ.get("NVIDIA_API_KEY")
        if not nvidia_api_key:
            raise ValueError("NVIDIA_API_KEY manquante.")
            
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=nvidia_api_key
        )
        self.model = "meta/llama-3.3-70b-instruct"

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
