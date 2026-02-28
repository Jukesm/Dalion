import asyncio
import time
import random
import threading
from database import SessionLocal, init_db, increment_with_lock
from models import Idea, User
from circuit_breaker import ollama_breaker, CircuitState
from cache import SlidingWindowRateLimiter, cache

async def test_circuit_breaker():
    print("\n--- Testando Circuit Breaker ---")
    
    async def failing_func():
        raise Exception("Erro Simulado")

    async def success_func():
        return "OK"

    print(f"Estado inicial: {ollama_breaker.state}")
    
    # Simular falhas para abrir o circuito
    for _ in range(4):
        try:
            await ollama_breaker.call(failing_func)
        except:
            pass
    
    print(f"Estado apos 4 falhas: {ollama_breaker.state}")
    
    try:
        await ollama_breaker.call(success_func)
    except Exception as e:
        print(f"Chamada bloqueada corretamente: {e}")

    # Forcar estado HALF-OPEN
    ollama_breaker.last_failure_time = time.monotonic() - 61
    print("Simulando passagem de tempo...")
    
    result = await ollama_breaker.call(success_func)
    print(f"Resultado em HALF-OPEN: {result}")
    print(f"Estado final: {ollama_breaker.state}")

def test_optimistic_lock():
    print("\n--- Testando Lock Otimista (Concorrencia) ---")
    init_db()
    db = SessionLocal()
    
    # Criar ideia de teste
    idea = Idea(title="Lock Test", description="Testing concurrency", user_id=1)
    db.add(idea)
    db.commit()
    idea_id = idea.id
    db.close()

    def heavy_incrementer(id):
        session = SessionLocal()
        for _ in range(10):
            increment_with_lock(session, Idea, id, "views")
        session.close()

    threads = []
    for _ in range(5): # 5 threads incrementando 10 vezes cada = 50 views
        t = threading.Thread(target=heavy_incrementer, args=(idea_id,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    db = SessionLocal()
    final_idea = db.query(Idea).filter(Idea.id == idea_id).first()
    print(f"Total esperado: 50 | Total real: {final_idea.views}")
    if final_idea.views == 50:
        print("[OK] Lock Otimista funcionou perfeitamente!")
    else:
        print("[FAIL] Falha na concorrencia!")
    db.close()

def test_cache_rate_limit():
    print("\n--- Testando Rate Limiter (Cache Fallback) ---")
    limiter = SlidingWindowRateLimiter("test_limit", limit=3, window_seconds=5)
    
    user_id = "user_123"
    print(f"Dando 5 requests para limite 3...")
    results = [limiter.is_allowed(user_id) for _ in range(5)]
    print(f"Resultados: {results}")
    
    if results == [True, True, True, False, False]:
        print("[OK] Rate Limiter funcionou!")
    else:
        print("[FAIL] Rate Limiter falhou!")

if __name__ == "__main__":
    # Rodar testes sincronos primeiro
    test_optimistic_lock()
    test_cache_rate_limit()
    
    # Rodar testes assincronos
    asyncio.run(test_circuit_breaker())
