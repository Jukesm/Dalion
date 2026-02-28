import time
from fastapi import Request
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
from logger import logger

# Métrica de Requisições
HTTP_REQUEST_COUNT = Counter(
    "http_requests_total", 
    "Total de requisições HTTP", 
    ["method", "endpoint", "status"]
)

# Métrica de Latência (Buckets ajustados para Ollama/IA)
HTTP_REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Latência das requisições em segundos",
    ["method", "endpoint"],
    buckets=[1, 2.5, 5, 10, 20, 30, 60, 90, 120]
)

# Métrica de Falhas do Ollama
OLLAMA_FAILURE_COUNT = Counter(
    "ollama_failures_total",
    "Total de falhas na API do Ollama",
    ["service"]
)

async def prometheus_middleware(request: Request, call_next):
    """Middleware para capturar métricas de todas as requisições."""
    start_time = time.time()
    method = request.method
    endpoint = request.url.path

    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        status_code = 500
        raise e
    finally:
        latency = time.time() - start_time
        
        # Registrar métricas
        HTTP_REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status_code).inc()
        HTTP_REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(latency)
        
    return response

def metrics_endpoint():
    """Retorna as métricas no formato do Prometheus."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
