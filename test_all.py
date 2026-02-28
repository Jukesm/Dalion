import requests
import time
import os

BASE_URL = "http://127.0.0.1:8000"
USER_EMAIL = f"test_user_{int(time.time())}@example.com"
PASSWORD = "testpassword123"

def test_flow():
    print("--- Iniciando Teste Geral do CEO IA BR ---\n")

    # 1. Registrar Usuário
    print("1. Testando Registro...")
    reg_res = requests.post(f"{BASE_URL}/register?email={USER_EMAIL}&password={PASSWORD}")
    if reg_res.status_code == 200:
        print("OK: Usuário registrado com sucesso.")
    else:
        print(f"Erro no registro: {reg_res.json()}")
        return

    # 2. Login
    print("\n2. Testando Login...")
    login_res = requests.post(f"{BASE_URL}/login?email={USER_EMAIL}&password={PASSWORD}")
    if login_res.status_code == 200:
        token = login_res.json()["access_token"]
        print("OK: Login realizado. Token obtido.")
    else:
        print(f"Erro no login: {login_res.json()}")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # 3. Pipeline Autônomo
    print("\n3. Testando Pipeline Autônomo (Pode demorar devido ao Ollama)...")
    pipe_res = requests.post(f"{BASE_URL}/auto-pipeline", headers=headers)
    if pipe_res.status_code == 200:
        data = pipe_res.json()
        print(f"OK: Pipeline executado: '{data['idea']}'")
        file_path = data["execution"]["file"]
        print(f"OK: Arquivo gerado em: {file_path}")
        
        # 4. Verificar Hospedagem
        print("\n4. Verificando Hospedagem da Landing Page...")
        public_url = f"{BASE_URL}/p/{os.path.basename(file_path)}"
        page_res = requests.get(public_url)
        if page_res.status_code == 200:
            print(f"OK: Landing Page ONLINE em: {public_url}")
        else:
            print("Erro ao acessar a página hospedada.")
    else:
        print(f"Erro no Pipeline: {pipe_res.text}")

    # 5. Growth Engine HQ
    print("\n5. Testando Growth Money Engine HQ (Análise Estratégica)...")
    growth_res = requests.post(f"{BASE_URL}/growth-engine", headers=headers, params={
        "title": "Creme de Rejuvenescimento Facial 50g",
        "description": "Creme com ácido hialurônico para peles maduras.",
        "cost": 15.0,
        "price": 89.0,
        "niche": "beleza"
    })
    if growth_res.status_code == 200:
        print("OK: Growth Engine HQ gerou a estratégia com sucesso.")
    else:
        print(f"Erro no Growth Engine: {growth_res.text}")

    print("\n--- Teste Concluído com Sucesso! ---")

if __name__ == "__main__":
    test_flow()
