# Memória Simplificada para Plano Free (Sem Transformers)
import os

def add_idea_to_memory(idea_id, title, description, target_audience):
    """
    Versão leve: Apenas loga a ideia. 
    Em sistemas com mais RAM, aqui usariamos busca vetorial.
    """
    print(f"Ideia {idea_id} registrada na memória leve.")

def search_similar_ideas(query_text, n_results=3):
    """
    Versão leve: Retorna lista vazia por enquanto para não travar o sistema.
    """
    return {"documents": [[]]}
