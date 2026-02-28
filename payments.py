import requests
import mercadopago

# Credenciais do App (Obtenha no Painel do Mercado Pago Developers)
CLIENT_ID = "SEU_CLIENT_ID"
CLIENT_SECRET = "SEU_CLIENT_SECRET"
REDIRECT_URI = "http://127.0.0.1:8000/mp-callback"

def exchange_code_for_token(code):
    """
    Troca o código de autorização do Mercado Pago por um Access Token.
    """
    url = "https://api.mercadopago.com/oauth/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "client_secret": CLIENT_SECRET,
        "client_id": CLIENT_ID,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI
    }
    
    try:
        response = requests.post(url, data=data, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Erro OAuth MP: {response.text}")
            return None
    except Exception as e:
        print(f"Erro na requisição OAuth: {e}")
        return None

def create_payment(title, price, access_token=None):
    """
    Cria uma preferência de pagamento.
    Se access_token for fornecido, usa a conta do usuário (SaaS).
    Caso contrário, usa o token padrão (Administrador).
    """
    # Token padrão de fallback se nenhum for passado
    token_to_use = access_token if access_token else "SUA_CHAVE_MESTRA_AQUI"
    
    sdk = mercadopago.SDK(token_to_use)
    
    preference_data = {
        "items": [
            {
                "title": title,
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": float(price)
            }
        ],
        "back_urls": {
            "success": "http://127.0.0.1:8000/dashboard",
            "failure": "http://127.0.0.1:8000/dashboard",
            "pending": "http://127.0.0.1:8000/dashboard"
        },
        "auto_return": "approved",
    }

    try:
        preference_response = sdk.preference().create(preference_data)
        if "response" in preference_response and "init_point" in preference_response["response"]:
            return preference_response["response"]["init_point"]
        return "#"
    except Exception as e:
        print(f"Erro ao criar link de pagamento: {e}")
        return "#"
