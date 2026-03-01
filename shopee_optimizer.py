from ai_provider import ai
from logger import logger

async def optimize_product(title, description):
    """
    Especialista em SEO e conversão para Shopee Brasil.
    Gera títulos, descrições e bullets otimizados usando IA.
    """
    prompt = f"""
    Você é um especialista em SEO e copy de alta conversão para Shopee Brasil.
    Melhore este anúncio para atrair mais cliques e vendas:

    Título Atual: {title}
    Descrição Atual: {description}

    Gere uma resposta estruturada contendo:
    1. Novo título otimizado (focado em palavras-chave de busca)
    2. Descrição altamente persuasiva (com gatilhos mentais)
    3. 5 Benefícios principais em bullet points
    4. 3 Variações de título para teste A/B
    5. FAQ com 3 perguntas comuns

    Responda em formato de texto limpo e organizado.
    """

    try:
        return await ai.generate(prompt)
    except Exception as e:
        logger.error(f"Erro na otimização: {e}")
        return f"Erro na otimização: {e}"
