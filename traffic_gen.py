import requests
from logger import logger

OLLAMA_URL = "http://localhost:11434/api/generate"

def generate_traffic_content(idea_title, idea_description, target_audience):
    """
    Gera conteúdo de tráfego (Instagram, TikTok, Ads) para uma ideia específica.
    """
    prompt = f"""
    Você é um estrategista de tráfego pago e social media marketing.
    Crie um "Pacote de Explosão de Tráfego" para o seguinte produto:

    Produto: {idea_title}
    Descrição: {idea_description}
    Público-alvo: {target_audience}

    Gere:
    1. LEGENDAS PARA INSTAGRAM/TIKTOK (3 variações: Curiosidade, Dor, Desejo)
    2. ROTEIRO DE REELS/TIKTOK (30 segundos focado em retenção)
    3. COPY PARA ANÚNCIO (Facebook/Instagram Ads - Formato AIDA)
    4. SUGESTÃO DE CRIATIVO (O que deve aparecer na imagem ou vídeo)
    5. HASHTAGS ESTRATÉGICAS

    Responda em Português do Brasil com uma estrutura clara e pronta para copiar e colar.
    """

    try:
        logger.info(f"Gerando conteúdo de tráfego para: {idea_title}")
        response = requests.post(OLLAMA_URL, json={
            "model": "mistral",
            "prompt": prompt,
            "stream": False
        }, timeout=90)
        
        if response.status_code == 200:
            content = response.json().get("response", "Erro ao extrair resposta do Ollama.")
            return content
        else:
            logger.error(f"Erro na API do Ollama: {response.text}")
            return "Erro ao gerar conteúdo de tráfego."
            
    except Exception as e:
        logger.error(f"Erro ao conectar com Ollama para tráfego: {e}")
        return f"Erro técnico: {e}"
