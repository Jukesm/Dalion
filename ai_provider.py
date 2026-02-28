import os
import requests
from logger import logger
from tenacity import retry, stop_after_attempt, wait_exponential

class AIProvider:
    def __init__(self):
        self.provider = os.getenv("AI_PROVIDER", "ollama").lower()
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
        self.model = os.getenv("AI_MODEL", "llama3-70b-8192" if self.provider == "groq" else "mistral")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate(self, prompt: str) -> str:
        if self.provider == "groq":
            return await self._call_groq(prompt)
        else:
            return await self._call_ollama(prompt)

    async def _call_groq(self, prompt: str) -> str:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Erro no Groq: {e}")
            raise e

    async def _call_ollama(self, prompt: str) -> str:
        try:
            response = requests.post(self.ollama_url, json={
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }, timeout=90)
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            logger.error(f"Erro no Ollama: {e}")
            raise e

# Instância única global
ai = AIProvider()
