import os
import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from ai_provider import ai
from database import SessionLocal
from models import Idea
from payments import create_payment
from logger import logger

from circuit_breaker import ollama_breaker


async def generate_sales_copy(title, description, target, price):
    prompt = f"""
    Você é um copywriter especialista em vendas no Brasil.
    Crie uma página de vendas altamente persuasiva para:

    Produto: {title}
    Público: {target}
    Descrição: {description}
    Preço: R${price}

    Gere:
    - Headline poderosa
    - Subheadline
    - 5 benefícios em bullet points
    - Seção problema
    - Seção solução
    - FAQ com 3 perguntas

    Responda em formato de texto limpo, sem metadados.
    """

    try:
        # Usa o AIProvider configurado (Groq ou Ollama) e o Circuit Breaker
        return await ollama_breaker.call(ai.generate, prompt)
    except Exception as e:
        logger.error(f"Erro ao gerar copy: {e}")
        raise e


def execute_idea(idea_id: int, db=None, access_token=None):
    if db is None:
        db = SessionLocal()
        close_db = True
    else:
        close_db = False

    idea = db.query(Idea).filter(Idea.id == idea_id).first()

    if not idea or idea.status != "approved":
        if close_db: db.close()
        return {"error": "Ideia não encontrada ou não aprovada"}

    os.makedirs("products", exist_ok=True)

    sales_copy = generate_sales_copy(
        idea.title,
        idea.description,
        idea.target_audience,
        idea.price
    )

    # Geração do link de pagamento
    payment_link = create_payment(idea.title, idea.price, access_token=access_token)

    file_name = f"lp_{idea.id}_{idea.title.replace(' ', '_').lower()}"
    file_path = f"products/{file_name}.html"

    # Convert markdown-style bullets and line breaks to HTML for better display
    formatted_copy = sales_copy.replace("\n", "<br>")

    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{idea.title}</title>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; line-height: 1.6; padding: 40px; max-width: 800px; margin: auto; background: #f4f7f6; color: #333; }}
            .container {{ background: #fff; padding: 40px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
            h1 {{ color: #2c3e50; font-size: 2.5em; text-align: center; }}
            .price-tag {{ font-size: 1.5em; font-weight: bold; color: #e74c3c; text-align: center; margin: 30px 0; }}
            .cta-button {{ display: block; width: 280px; margin: 0 auto; padding: 20px; text-align: center; background: #27ae60; color: #fff; text-decoration: none; font-size: 1.3em; font-weight: bold; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>{idea.title}</h1>
            <div class="copy-content">{formatted_copy}</div>
            <div class="price-tag">Investimento: R${idea.price:.2f}</div>
            <a href="{payment_link}" class="cta-button" target="_blank">Comprar Agora</a>
            
            <script>
                fetch('/track-view/{idea.id}', {{ method: 'GET', keepalive: true }}).catch(() => {{}});
            </script>
        </div>
    </body>
    </html>
    """

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    idea.status = "executed"
    db.commit()
    if close_db: db.close()

    return {"message": "Landing page criada", "file": file_path}
