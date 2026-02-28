import os
import redis
from rq import Queue, Retry
from logger import pipeline_logger

# Configuração do Redis para o RQ
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

try:
    redis_conn = redis.from_url(REDIS_URL)
    # Filas separadas por peso
    queue_pipeline = Queue("pipeline", connection=redis_conn)
    queue_tracking = Queue("tracking", connection=redis_conn)
    queue_notifications = Queue("notifications", connection=redis_conn)
    USE_QUEUES = True
except Exception as e:
    pipeline_logger.warning(f"RQ Worker indisponível ({e}). Usando modo síncrono.")
    USE_QUEUES = False

def enqueue_pipeline_job(func, *args, **kwargs):
    """
    Enfileira um job de pipeline com identificador único para deduplicação.
    Ex: f"pipeline:{idea_id}"
    """
    job_id = kwargs.pop("job_id", None)
    
    if USE_QUEUES:
        pipeline_logger.info(f"Enfileirando job em background: {job_id or func.__name__}")
        return queue_pipeline.enqueue(
            func, 
            args=args, 
            kwargs=kwargs, 
            job_id=job_id,
            retry=Retry(max=3, interval=[10, 30, 60])
        )
    else:
        # Fallback síncrono para desenvolvimento
        return func(*args, **kwargs)

def enqueue_tracking_job(func, *args, **kwargs):
    """Enfileira job leve de estatísticas."""
    if USE_QUEUES:
        return queue_tracking.enqueue(func, args=args, kwargs=kwargs)
    else:
        return func(*args, **kwargs)
