import os
import time
import json
import redis
from logger import logger

class _InMemoryFallback:
    """Fallback simples em memória caso o Redis esteja offline."""
    def __init__(self):
        self._data = {}
        self._expires = {}

    def get(self, key):
        if key in self._expires and self._expires[key] < time.time():
            self.delete(key)
            return None
        return self._data.get(key)

    def set(self, key, value, ex=None):
        self._data[key] = value
        if ex:
            self._expires[key] = time.time() + ex

    def delete(self, key):
        self._data.pop(key, None)
        self._expires.pop(key, None)

    def incr(self, key):
        val = int(self.get(key) or 0) + 1
        self.set(key, str(val))
        return val

# Configuração Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

try:
    cache = redis.from_url(REDIS_URL, decode_responses=True)
    cache.ping()
    logger.info("Conexão com Redis estabelecida com sucesso.")
except Exception as e:
    logger.warning(f"Redis indisponível ({e}). Usando fallback em memória.")
    cache = _InMemoryFallback()

class SlidingWindowRateLimiter:
    """Implementa Rate Limiting via janela deslizante."""
    def __init__(self, key_prefix, limit, window_seconds):
        self.key_prefix = key_prefix
        self.limit = limit
        self.window = window_seconds

    def is_allowed(self, identifier):
        key = f"rate:{self.key_prefix}:{identifier}"
        try:
            # Lógica simplificada: para fallback em memória usamos incremental
            # Para produção real Redis, usaríamos scripts Lua para atonicidade
            current = int(cache.get(key) or 0)
            if current >= self.limit:
                return False
            
            cache.set(key, current + 1, ex=self.window)
            return True
        except Exception:
            # Em caso de erro na infra de cache, permitimos a requisição (fail-open)
            return True
