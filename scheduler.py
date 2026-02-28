import asyncio
import time
from datetime import datetime, timedelta
from database import SessionLocal
from models import User
from logger import pipeline_logger
import traceback

async def scheduler_loop():
    """
    Ticker horário resiliente.
    Em vez de intervalo fixo, acorda a cada hora e verifica quem é elegível no banco.
    """
    pipeline_logger.info("Scheduler Loop iniciado (Check de elegibilidade persistente).")
    
    while True:
        try:
            db = SessionLocal()
            now = datetime.utcnow()
            
            # Busca usuários ativos
            users = db.query(User).filter(User.is_active == True).all()
            
            for user in users:
                try:
                    should_run = False
                    if not user.last_run_at:
                        should_run = True # Nunca rodou
                    else:
                        last_run = datetime.fromisoformat(user.last_run_at)
                        if (now - last_run) >= timedelta(days=7):
                            should_run = True
                    
                    if should_run:
                        pipeline_logger.info(f"Usuário {user.email} está elegível para o pipeline semanal.")
                        # Importação local para evitar import circular
                        from main import run_auto_pipeline_internal
                        
                        # Executa o pipeline
                        run_auto_pipeline_internal(user, db)
                        
                        # ATUALIZAÇÃO SÓ APÓS SUCESSO (Persistência)
                        user.last_run_at = now.isoformat()
                        db.commit()
                        pipeline_logger.info(f"Pipeline concluído e timestamp persistido para {user.email}")
                
                except Exception as e:
                    db.rollback()
                    pipeline_logger.error(f"Erro no pipeline do usuário {user.email}: {e}")
                    # Não atualiza last_run_at em caso de falha -> Causará retry no próximo ciclo
            
            db.close()
            
        except Exception as e:
            pipeline_logger.error(f"Erro crítico no loop do scheduler: {e}")
            
        # Acorda a cada 1 hora para verificar elegibilidade
        await asyncio.sleep(3600)

def start_scheduler():
    """Mantido por retrocompatibilidade, mas agora usa o loop assíncrono do FastAPI."""
    pass
