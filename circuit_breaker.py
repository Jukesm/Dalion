import asyncio
import time
from enum import Enum
from logger import logger

class CircuitState(Enum):
    CLOSED = "CLOSED"     # Tudo ok, chamadas permitidas
    OPEN = "OPEN"         # Muitas falhas, chamadas bloqueadas
    HALF_OPEN = "HALF_OPEN" # Testando se o serviço voltou

class CircuitBreaker:
    def __init__(self, name, failure_threshold=5, recovery_timeout=30):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.last_failure_time = 0

    def _check_recovery(self):
        """Verifica se deve passar de OPEN para HALF_OPEN."""
        if self.state == CircuitState.OPEN:
            if time.monotonic() - self.last_failure_time >= self.recovery_timeout:
                logger.info(f"Circuit Breaker [{self.name}]: Entrando em estado HALF-OPEN")
                self.state = CircuitState.HALF_OPEN

    async def call(self, func, *args, **kwargs):
        self._check_recovery()

        if self.state == CircuitState.OPEN:
            logger.warning(f"Circuit Breaker [{self.name}]: Chamada bloqueada! (Circuito ABERTO)")
            raise Exception(f"Serviço {self.name} temporariamente indisponível (Circuit Breaker OPEN)")

        try:
            # Se for assíncrona, fazemos o await
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Sucesso! Resetamos falhas se estávamos em HALF-OPEN
            if self.state == CircuitState.HALF_OPEN:
                logger.info(f"Circuit Breaker [{self.name}]: Recuperado com sucesso! (CLOSED)")
                self.state = CircuitState.CLOSED
                self.failures = 0
                
            return result

        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.monotonic()
            
            logger.error(f"Falha detectada no serviço [{self.name}]: {e}")

            if self.failures >= self.failure_threshold:
                if self.state != CircuitState.OPEN:
                    logger.critical(f"Circuit Breaker [{self.name}]: ABRINDO CIRCUITO após {self.failures} falhas.")
                    self.state = CircuitState.OPEN
            
            raise e

# Instância global para o Ollama
ollama_breaker = CircuitBreaker(name="OllamaService", failure_threshold=3, recovery_timeout=60)
