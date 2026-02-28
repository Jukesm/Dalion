import asyncio
import hashlib
import hmac
import json
import os
import shutil
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import (
    Depends, FastAPI, File, Header, HTTPException,
    Request, UploadFile, status
)
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from database import engine, SessionLocal
from models import Base, Idea, User
from planner import generate_idea
from memory_manager import save_memory
from executor import execute_idea
from traffic_gen import generate_traffic_content
from auth import hash_password, verify_password, create_access_token, SECRET_KEY, ALGORITHM
from jose import jwt, JWTError
from logger import logger, pipeline_logger
from pdf_processor import ingest_pdf, KNOWLEDGE_DIR
from scheduler import scheduler_loop
from metrics_collector import prometheus_middleware, metrics_endpoint
from jobs import enqueue_pipeline_job, enqueue_tracking_job
from shopee_optimizer import optimize_product
from growth_engine import growth_money_engine
from payments import exchange_code_for_token, CLIENT_ID, REDIRECT_URI

# ─────────────────────────────────────────────
# CONFIGURAÇÃO
# ─────────────────────────────────────────────
KNOWLEDGE_BASE_DIR = Path(KNOWLEDGE_DIR)
MAX_UPLOAD_SIZE_MB = 10
MAX_UPLOAD_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

MP_WEBHOOK_SECRET = os.getenv("MP_WEBHOOK_SECRET", "CHANGE_ME_IN_PRODUCTION")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "CHANGE_ME_IN_PRODUCTION")

# ─────────────────────────────────────────────
# RATE LIMITER
# ─────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

# ─────────────────────────────────────────────
# LIFESPAN — Scheduler em background
# ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa banco e scheduler. Cancela o scheduler no shutdown."""
    Base.metadata.create_all(bind=engine)
    logger.info("Banco de dados inicializado.")
    scheduler_task = asyncio.create_task(scheduler_loop())
    logger.info("Scheduler iniciado em background.")
    yield
    scheduler_task.cancel()
    logger.info("Scheduler encerrado.")

# ─────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────
app = FastAPI(
    title="CEO IA BR",
    version="2.0.0-hardened",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.middleware("http")(prometheus_middleware)

@app.get("/metrics")
def get_metrics():
    return metrics_endpoint()

@app.get("/health")
def health_check():
    return {
        "status": "healthy", 
        "version": "4.1-deploy-groq",
        "provider": os.getenv("AI_PROVIDER", "ollama")
    }

# Criar pasta de produtos se não existir
os.makedirs("products", exist_ok=True)

# Servir as Landing Pages geradas publicamente em /p/nome-do-arquivo.html
app.mount("/p", StaticFiles(directory="products"), name="products")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency to get current user from token
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        logger.warning(f"Acesso não autorizado ao endpoint de admin por user_id={current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores"
        )
    return current_user

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
        <head>
            <title>CEO IA BR - Hardened</title>
            <style>
                body { 
                    font-family: 'Inter', Arial, sans-serif; 
                    background: #0f172a; 
                    color: white; 
                    text-align: center; 
                    padding: 60px;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    height: 80vh;
                }
                h1 { font-size: 4rem; margin-bottom: 10px; }
                p { font-size: 1.5rem; color: #94a3b8; max-width: 600px; margin-bottom: 40px; }
                button {
                    background: #22c55e;
                    border: none;
                    padding: 18px 40px;
                    font-size: 20px;
                    color: white;
                    cursor: pointer;
                    border-radius: 12px;
                    font-weight: bold;
                    transition: all 0.3s ease;
                    box-shadow: 0 4px 20px rgba(34, 197, 94, 0.4);
                }
                button:hover {
                    background: #16a34a;
                    transform: translateY(-2px);
                    box-shadow: 0 6px 25px rgba(34, 197, 94, 0.5);
                }
            </style>
        </head>
        <body>
            <h1>🚀 CEO IA BR</h1>
            <p>Versão 2.0.0 (Hardened & Resilient)</p>
            <br>
            <a href="/docs">
                <button>Entrar no Sistema</button>
            </a>
        </body>
    </html>
    """

@app.post("/register")
def register(email: str, password: str, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")
        
    user = User(email=email, hashed_password=hash_password(password))
    # Primeiro usuário vira admin no MVP (opcional)
    if db.query(User).count() == 0:
        user.is_admin = True
        
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "Usuário criado com sucesso", "id": user.id}

@app.post("/login")
def login(email: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos")
    
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/generate-idea")
def create_idea(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    idea = generate_idea(db=db) # Pass db to generate_idea
    idea.user_id = current_user.id
    db.add(idea)
    db.commit()
    db.refresh(idea)
    
    save_memory(f"Idea criada por {current_user.email}: {idea.title}", level="hot")
    return {
        "id": idea.id,
        "title": idea.title,
        "status": idea.status
    }

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ideas = db.query(Idea).filter(Idea.user_id == current_user.id).all()

    html = f"""
    <html>
    <head>
        <title>CEO IA BR - Dashboard SaaS</title>
        <style>
            body {{ font-family: 'Inter', system-ui; padding: 40px; background: #f0f2f5; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; }}
            .card {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .status {{ font-weight: bold; color: #2563eb; }}
            .btn {{ display: inline-block; padding: 8px 16px; background: #22c55e; color: white; border-radius: 4px; text-decoration: none; border: none; cursor: pointer; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Dashboard CEO IA BR</h1>
            <p>Logado como: <strong>{current_user.email}</strong></p>
        </div>
        <div>
    """

    for idea in ideas:
        file_name = idea.title.replace(" ", "_").lower()
        public_url = f"/p/{file_name}.html"
        
        link_html = f"<a href='{public_url}' target='_blank' style='color: #10b981;'>Ver Página Publicada</a>" if idea.status == "executed" else ""

        html += f"""
        <div class='card'>
            <h3>{idea.title}</h3>
            <p>Status: <span class='status'>{idea.status}</span></p>
            {link_html}
            <br><br>
            <form action='/execute/{idea.id}' method='post' style='display:inline;'><button type='submit' class='btn'>Executar / Republicar</button></form>
        </div>
        """
    
    if not ideas:
        html += "<p>Nenhuma ideia gerada ainda.</p>"

    html += "</div></body></html>"
    return html

@app.post("/approve/{idea_id}")
def approve_idea(idea_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    idea = db.query(Idea).filter(Idea.id == idea_id, Idea.user_id == current_user.id).first()
    if not idea:
        raise HTTPException(status_code=404, detail="Ideia não encontrada")
    idea.status = "approved"
    db.commit()
    return {"message": "Ideia aprovada"}

from shopee_optimizer import optimize_product

@app.post("/optimize-shopee")
def optimize_shopee(title: str, description: str, current_user: User = Depends(get_current_user)):
    """
    Motor 2: Otimização Shopee.
    Reescreve títulos e descrições para conversão e SEO.
    """
    result = optimize_product(title, description)
    save_memory(f"Shopee Optimizer usado por {current_user.email}: {title}", level="hot")
    return {"optimized": result}

from growth_engine import growth_money_engine

@app.post("/growth-engine")
def run_growth_engine(
    title: str, 
    description: str, 
    cost: float = None, 
    price: float = None, 
    niche: str = "beleza",
    current_user: User = Depends(get_current_user)
):
    """
    HQ: Motor de Crescimento e Renda.
    Executa a estratégia de 5 fases para maximizar lucros Shopee e criar produtos digitais.
    """
    result = growth_money_engine(title, description, cost, price, niche)
    save_memory(f"Growth Engine HQ usado por {current_user.email} para: {title}", level="hot")
    return {"strategy": result}

@app.get("/connect-mp")
def connect_mercadopago(current_user: User = Depends(get_current_user)):
    """
    Redireciona o usuário para autorizar o app no Mercado Pago.
    """
    auth_url = f"https://auth.mercadopago.com.br/authorization?client_id={CLIENT_ID}&response_type=code&platform_id=mp&redirect_uri={REDIRECT_URI}"
    return {"url": auth_url}

@app.get("/mp-callback")
def mercadopago_callback(code: str, db: Session = Depends(get_db)):
    """
    Recebe o código do MP, troca por token e salva no usuário.
    Nota: Em um sistema real, você passaria o user_id no 'state' do OAuth.
    Para este MVP, vamos assumir o último usuário logado ou pedir login.
    """
    token_data = exchange_code_for_token(code)
    if not token_data:
        raise HTTPException(status_code=400, detail="Erro ao conectar com Mercado Pago")
    
    # Exemplo: Atualizando o primeiro usuário para teste (ou use o state para identificar)
    user = db.query(User).first() 
    if user:
        user.mp_access_token = token_data.get("access_token")
        user.mp_refresh_token = token_data.get("refresh_token")
        user.mp_user_id = str(token_data.get("user_id"))
        db.commit()
        
    return {"message": "Mercado Pago conectado com sucesso!"}

@app.post("/execute/{idea_id}")
def run_execution(idea_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Agora passamos o token do usuário para o executor
    return execute_idea(idea_id, db=db, access_token=current_user.mp_access_token)

# Função interna para ser chamada pelo agendador ou pelo endpoint
def run_auto_pipeline_internal(user: User, db: Session):
    """Lógica central do pipeline autônomo."""
    try:
        # 1. Gerar Ideia
        idea = generate_idea(db=db)
        idea.user_id = user.id
        
        # 2. Aprovar Automaticamente
        idea.status = "approved"
        db.commit()
        
        # 3. Executar (Gerar Copy e HTML usando o token do MP do usuário)
        execution_result = execute_idea(idea.id, db=db, access_token=user.mp_access_token)
        
        save_memory(f"Pipeline Autônomo processado: {idea.title} para {user.email}", level="hot")
        return {
            "idea": idea.title,
            "execution": execution_result
        }
    except Exception as e:
        pipeline_logger.error(f"Falha no pipeline interno para {user.email}: {e}")
        raise e

@app.post("/auto-pipeline")
@limiter.limit("1/minute")
def run_auto_pipeline(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Enfileira para background worker com ID único por ideia/usuário
    job_id = f"pipeline:{current_user.id}:{int(time.time()/3600)}" # Um job por hora max
    enqueue_pipeline_job(run_auto_pipeline_internal, current_user, db, job_id=job_id)
    return {"message": "Pipeline enfileirado para processamento em background"}

import hmac
import hashlib

# Em produção, pegue isso do config/env
MP_WEBHOOK_SECRET = os.getenv("MP_WEBHOOK_SECRET", "SUA_CHAVE_SECRETA_DO_WEBHOOK")

def process_conversion_bg(idea_id: int):
    """Tarefa de background para processar conversão."""
    db = SessionLocal()
    try:
        increment_with_lock(db, Idea, idea_id, "conversions")
    finally:
        db.close()

@app.post("/webhook/mercadopago")
async def mercadopago_webhook(request: Request, x_signature: Optional[str] = Header(None), db: Session = Depends(get_db)):
    body = await request.body()
    
    if MP_WEBHOOK_SECRET != "CHANGE_ME_IN_PRODUCTION" and x_signature:
        expected_sig = hmac.new(MP_WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(x_signature.lower(), expected_sig.lower()):
            raise HTTPException(status_code=403, detail="Assinatura inválida")

    payload = await request.json()
    if payload.get("type") == "payment":
        idea_id = payload.get("data", {}).get("external_reference")
        if idea_id:
            # Move processamento pesado/concorrente para background
            enqueue_tracking_job(process_conversion_bg, int(idea_id))
            
    return {"status": "ok"}

@app.post("/upload-knowledge")
@limiter.limit("2/minute")
async def upload_pdf(
    request: Request,
    file: UploadFile = File(...), 
    current_user: User = Depends(get_current_user)
):
    """Endpoint SEGURO para enviar PDFs e dar 'conhecimento' ao sistema."""
    # 1. Validar tipo de arquivo
    if file.content_type != "application/pdf" and not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são permitidos.")
    
    # 2. Validar tamanho (10MB max)
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Arquivo muito grande. Limite de 10MB.")
    
    file_path = os.path.join(KNOWLEDGE_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(content)
    
    # Processar imediatamente
    success = ingest_pdf(file_path)
    if success:
        return {"message": f"Conhecimento de '{file.filename}' absorvido com sucesso!"}
    else:
        return {"message": "Erro ao processar o PDF.", "error": True}

def process_view_bg(idea_id: int):
    """Tarefa de background para processar visualização."""
    db = SessionLocal()
    try:
        increment_with_lock(db, Idea, idea_id, "views")
    finally:
        db.close()

@app.get("/track-view/{idea_id}")
async def track_view(idea_id: int):
    """Tracking resiliente usando Queue + Lock Otimista."""
    enqueue_tracking_job(process_view_bg, idea_id)
    from fastapi import Response
    return Response(content=TRANSPARENT_PIXEL, media_type="image/gif")

@app.get("/metrics/summary", tags=["Métricas"])
@limiter.limit("30/minute")
async def metrics_summary(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Painel de métricas com comparativo semanal e taxa de crescimento.
    """
    now_ts = datetime.utcnow().timestamp()
    week_ago_ts = now_ts - (7 * 24 * 3600)
    two_weeks_ts = now_ts - (14 * 24 * 3600)

    # ── Total absoluto ────────────────────────────────────────────────────────
    all_ideas = db.query(Idea).filter(Idea.user_id == current_user.id).all()

    total_views       = sum(i.views       for i in all_ideas)
    total_conversions = sum(i.conversions for i in all_ideas)
    total_ideas       = len(all_ideas)
    
    # ── Comparativo semanal ───────────────────────────────────────────────────
    recent_ideas = [i for i in all_ideas if i.created_at >= week_ago_ts]
    prev_ideas   = [i for i in all_ideas if two_weeks_ts <= i.created_at < week_ago_ts]

    views_recent = sum(i.views for i in recent_ideas)
    views_prev   = sum(i.views for i in prev_ideas)

    def calculate_growth(current, previous):
        if previous == 0:
            return "+100%" if current > 0 else "0%"
        rate = ((current - previous) / previous) * 100
        return f"{'+' if rate >= 0 else ''}{rate:.1f}%"

    # ── Melhor ideia ──────────────────────────────────────────────────────────
    best_idea = max(all_ideas, key=lambda i: i.views, default=None)

    return {
        "totals": {
            "ideas": total_ideas,
            "views": total_views,
            "conversions": total_conversions,
            "avg_conversion_rate": f"{(total_conversions/total_views*100):.2f}%" if total_views > 0 else "0%",
        },
        "weekly_performance": {
            "current_week_views": views_recent,
            "previous_week_views": views_prev,
            "growth_rate": calculate_growth(views_recent, views_prev),
        },
        "best_performer": {
            "title": best_idea.title if best_idea else "N/A",
            "views": best_idea.views if best_idea else 0,
            "conversions": best_idea.conversions if best_idea else 0
        }
    }

@app.post("/generate-traffic/{idea_id}")
@limiter.limit("5/minute")
def create_traffic_assets(
    request: Request,
    idea_id: int, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Gera sugestões de posts e anúncios para uma ideia."""
    idea = db.query(Idea).filter(Idea.id == idea_id, Idea.user_id == current_user.id).first()
    if not idea:
        raise HTTPException(status_code=404, detail="Ideia não encontrada")
    
    package = generate_traffic_content(idea.title, idea.description, idea.target_audience)
    return {"traffic_assets": package}
