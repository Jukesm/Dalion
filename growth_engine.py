from ai_provider import ai
from logger import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from circuit_breaker import ollama_breaker

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=15))
async def growth_money_engine(product_title, product_description, cost_price=None, selling_price=None, niche="beleza"):
    """
    Motor de Crescimento Avançado: Transforma produtos reais em estratégias de elite e novos produtos digitais.
    """
    
    prompt = f"""
Você é um estrategista de crescimento focado em maximizar lucro na Shopee Brasil e transformar estratégias vencedoras em produtos digitais escaláveis.

Seu único objetivo é: AUMENTAR LUCRO E GERAR NOVA RENDA.

========================================
DADOS DO PRODUTO
========================================
Nicho: {niche}
Título atual: {product_title}
Descrição atual: {product_description}
Custo estimado: {cost_price if cost_price else 'Não informado'}
Preço atual: {selling_price if selling_price else 'Não informado'}

========================================
FASE 1 — OTIMIZAÇÃO PARA SHOPEE
========================================

1. Novo título otimizado para SEO Shopee Brasil
2. Descrição persuasiva focada em transformação e desejo
3. 5 benefícios emocionais fortes
4. 3 variações de título para teste
5. Frase poderosa para imagem principal
6. Roteiro de vídeo de 30 segundos
7. Sugestão de kit/combinação para aumentar ticket médio
8. Estratégia de escassez ou urgência

========================================
FASE 2 — ANÁLISE ESTRATÉGICA
========================================

1. Simulação de como concorrentes estariam vendendo esse produto
2. Oportunidade de diferenciação
3. Principais objeções do cliente e como quebrá-las
4. Ajuste de posicionamento para parecer mais premium

========================================
FASE 3 — PRECIFICAÇÃO E MARGEM
========================================

Se custo e preço foram fornecidos:
- Calcule margem estimada
- Sugira preço psicológico ideal
- Sugira versão premium
- Sugira versão econômica
- Estratégia para aumentar lucro sem perder conversão

Se não foram fornecidos:
- Estime faixa ideal de preço para o nicho {niche}

========================================
FASE 4 — REMARKETING
========================================

1. Mensagem automática para carrinho abandonado
2. Mensagem para cliente que comprou (incentivo recompra)
3. Ideia de campanha para Instagram ou TikTok

========================================
FASE 5 — TRANSFORMAÇÃO EM PRODUTO DIGITAL
========================================

Agora pense como dono de SaaS.

Crie um produto digital que ajude outros vendedores do nicho {niche} a aplicar essa estratégia.

Entregue:
1. Nome do produto
2. Promessa forte
3. Estrutura do que ele entrega
4. Preço sugerido
5. Modelo de assinatura
6. Ideia de upsell
7. Estratégia de lançamento simples
8. Projeção simples de faturamento mensal

========================================

Responda de forma estruturada, clara e prática em Português do Brasil.
Foque em lucro, diferenciação e escala.
"""

    try:
        # Usa o Circuit Breaker para proteger a chamada através do AIProvider
        response_text = await ollama_breaker.call(ai.generate, prompt)
        return response_text
    except Exception as e:
        logger.error(f"Erro no Motor de Crescimento: {e}")
        raise e
