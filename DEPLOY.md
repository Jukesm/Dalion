# 🚀 CEO IA BR - Guia de Deploy Rápido

## 1. Pré-requisitos (Grátis)
- **Groq Cloud**: [console.groq.com](https://console.groq.com) (Pegue sua API Key).
- **Upstash Redis**: [upstash.com](https://upstash.com) (Crie um DB Redis e copie a `REDIS_URL`).
- **Render**: [render.com](https://render.com) (Para hospedagem da API e DB).

## 2. Passo a Passo

### Parte A: GitHub
1. Crie um repositório **Privado** no seu GitHub.
2. `git init`
3. `git add .`
4. `git commit -m "Deploy v4.0"`
5. `git push origin main`

### Parte B: Render
1. Vá em **Dashboard** -> **New** -> **Blueprint**.
2. Conecte seu repositório do GitHub.
3. O Render vai ler o arquivo `render.yaml`.
4. Ele pedirá 3 variáveis:
   - `GROQ_API_KEY`: A chave que você pegou no Groq.
   - `REDIS_URL`: A URL do Upstash (ex: `rediss://default:xxx@upstash.com:6379`).
   - `SECRET_KEY`: Uma senha forte aleatória para seus tokens JWT.

## 3. Comandos Úteis
- **Shell do Render**: Para criar o primeiro usuário admin se não houver interface:
  `python -c "from database import SessionLocal; from models import User; from auth import hash_password; db=SessionLocal(); u=User(email='admin@seuemail.com', hashed_password=hash_password('suasenha'), is_admin=True); db.add(u); db.commit()"`

## 4. Verificar Saúde
Acesse `https://seu-app.onrender.com/health` para confirmar se está online.
