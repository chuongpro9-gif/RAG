import os
import requests

class OllamaClient:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b")
        
    def check_health(self):
        try:
            res = requests.get(f"{self.base_url}/api/tags", timeout=2)
            if res.status_code == 200:
                models = [m["name"] for m in res.json().get("models", [])]
                return True, models
        except Exception:
            return False, []
        return False, []
        
    def generate(self, prompt, temperature=0.2):
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        try:
            res = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=60)
            if res.status_code == 200:
                return res.json().get("response", "")
            return f"Ollama Error: HTTP {res.status_code}"
        except Exception as e:
            return f"Ollama Connection Error: {str(e)}"
