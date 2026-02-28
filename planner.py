import requests
import json
import re
from models import Idea
from vector_memory import add_idea_to_memory

OLLAMA_URL = "http://localhost:11434/api/generate"

def generate_idea(db=None):
    prompt = """
    Você é um CEO de IA focado no Brasil.
    Gere uma ideia de produto digital lucrativo.
    Responda APENAS em JSON no formato:
    {
        "title": "",
        "target_audience": "",
        "description": "",
        "price": 0
    }
    """

    try:
        response = requests.post(OLLAMA_URL, json={
            "model": "mistral",
            "prompt": prompt,
            "stream": False
        }, timeout=30)
        
        data = response.json()["response"]
        json_match = re.search(r'\{.*\}', data, re.DOTALL)
        idea_data = json.loads(json_match.group()) if json_match else json.loads(data)

    except Exception as e:
        print(f"Erro ao gerar ideia: {e}")
        idea_data = {
            "title": "Produto de Backup Automático",
            "target_audience": "Empreendedores",
            "description": "Sistema automático de backup em nuvem para PMEs brasileiras.",
            "price": 97.0
        }

    idea = Idea(**idea_data)
    
    if db:
        db.add(idea)
        db.commit()
        db.refresh(idea)
        try:
            add_idea_to_memory(idea.id, idea.title, idea.description, idea.target_audience)
        except: pass
        
    return idea
