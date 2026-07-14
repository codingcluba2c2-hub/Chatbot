import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class CircuitBreakerState:
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class CircuitBreaker:
    """
    Stateful circuit breaker for external LLM API calls.
    Tracks consecutive failures and cooldown periods to prevent cascaded failures
    or excessive rate limit API penalties.
    """
    def __init__(self, failure_threshold: int = 3, cooldown_seconds: int = 60):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        
        self.state = CircuitBreakerState.CLOSED
        self.consecutive_failures = 0
        self.last_failure_time: Optional[float] = None
        self.retry_after: Optional[float] = None

    def record_success(self):
        """Reset state on successful API call."""
        if self.state != CircuitBreakerState.CLOSED:
            logger.info("Circuit Breaker CLOSED (Recovery successful).")
        self.state = CircuitBreakerState.CLOSED
        self.consecutive_failures = 0
        self.last_failure_time = None
        self.retry_after = None

    def record_failure(self, retry_after: Optional[int] = None):
        """Record a failure and optionally open the circuit."""
        self.consecutive_failures += 1
        self.last_failure_time = time.time()
        
        if retry_after:
            # Respect explicit 429 Retry-After headers if available
            self.retry_after = time.time() + retry_after
        else:
            self.retry_after = time.time() + self.cooldown_seconds
            
        if self.state == CircuitBreakerState.CLOSED and self.consecutive_failures >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.warning(f"Circuit Breaker OPENED after {self.consecutive_failures} consecutive failures. Cooldown: {self.cooldown_seconds}s.")
        elif self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
            logger.warning("Circuit Breaker OPENED (Half-Open request failed).")

    def is_allowed(self) -> bool:
        """Check if request is allowed based on current state and cooldowns."""
        if self.state == CircuitBreakerState.CLOSED:
            return True
            
        if self.state == CircuitBreakerState.OPEN:
            if self.retry_after and time.time() >= self.retry_after:
                self.state = CircuitBreakerState.HALF_OPEN
                logger.info("Circuit Breaker HALF-OPEN (Testing recovery).")
                return True
            return False
            
        # HALF_OPEN allows exactly one request through to test recovery
        if self.state == CircuitBreakerState.HALF_OPEN:
            return True
            
        return True

# Singleton instance to be used across the application
llm_circuit_breaker = CircuitBreaker()
