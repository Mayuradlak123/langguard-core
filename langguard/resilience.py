import time
import pybreaker
from .logger import logger

class SeniorCircuitListener(pybreaker.CircuitBreakerListener):
    def state_change(self, cb, old_state, new_state):
        msg = f"🚨 Circuit Breaker '{cb.name}' changed from {old_state.name} to {new_state.name}"
        logger.warning(msg)

# Initialize breakers
llm_breaker = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=60, name="Groq-LLM", listeners=[SeniorCircuitListener()])
chroma_breaker = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=30, name="ChromaDB", listeners=[SeniorCircuitListener()])
neo4j_breaker = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=30, name="Neo4j", listeners=[SeniorCircuitListener()])

def with_breaker(breaker, fallback_func=None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return breaker.call(func, *args, **kwargs)
            except Exception as e:
                logger.error(f"❌ Breaker '{breaker.name}' caught: {str(e)}")
                if fallback_func:
                    return fallback_func(*args, **kwargs)
                raise e
        return wrapper
    return decorator

# Fallbacks
def llm_fallback(*args, **kwargs): return type('obj', (object,), {'content': "The AI service is currently unavailable. (Circuit Open)"})
def chroma_fallback(*args, **kwargs): logger.error("ChromaDB Fallback triggered"); return None
def neo4j_fallback(*args, **kwargs): logger.error("Neo4j Fallback triggered"); return None
