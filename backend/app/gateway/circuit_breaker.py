"""
Circuit Breaker Pattern

Prevents cascading failures when a provider is unhealthy.
States:
- CLOSED: Normal operation, requests pass through
- OPEN: Provider is failing, requests immediately rejected
- HALF_OPEN: Testing recovery, limited requests allowed
"""

import time
from typing import Dict

import structlog

from app.gateway.models import CircuitState, Provider

logger = structlog.get_logger(__name__)


class CircuitBreaker:
    """
    Circuit breaker for LLM provider calls.

    Tracks failures per provider and transitions between states
    to prevent wasting resources on failing providers.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 2,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        # State per provider
        self._states: Dict[str, CircuitState] = {}
        self._failure_counts: Dict[str, int] = {}
        self._last_failure_time: Dict[str, float] = {}
        self._half_open_calls: Dict[str, int] = {}

    def can_execute(self, provider: str) -> bool:
        """
        Check if a request to this provider is allowed.

        Returns True if the circuit is closed or half-open
        with available test slots.
        """
        state = self._states.get(provider, CircuitState.CLOSED)

        if state == CircuitState.CLOSED:
            return True

        if state == CircuitState.OPEN:
            # Check if recovery timeout has elapsed
            last_failure = self._last_failure_time.get(provider, 0)
            if time.time() - last_failure >= self.recovery_timeout:
                # Transition to half-open
                self._states[provider] = CircuitState.HALF_OPEN
                self._half_open_calls[provider] = 0
                logger.info(
                    "Circuit breaker: OPEN -> HALF_OPEN",
                    provider=provider,
                )
                return True
            return False

        if state == CircuitState.HALF_OPEN:
            calls = self._half_open_calls.get(provider, 0)
            return calls < self.half_open_max_calls

        return True

    def record_success(self, provider: str) -> None:
        """Record a successful call. Resets circuit to CLOSED."""
        state = self._states.get(provider, CircuitState.CLOSED)

        if state == CircuitState.HALF_OPEN:
            logger.info(
                "Circuit breaker: HALF_OPEN -> CLOSED",
                provider=provider,
            )

        self._states[provider] = CircuitState.CLOSED
        self._failure_counts[provider] = 0
        self._half_open_calls[provider] = 0

    def record_failure(self, provider: str) -> None:
        """Record a failed call. May open the circuit."""
        state = self._states.get(provider, CircuitState.CLOSED)

        if state == CircuitState.HALF_OPEN:
            # Failed during recovery test - go back to open
            self._states[provider] = CircuitState.OPEN
            self._last_failure_time[provider] = time.time()
            logger.warning(
                "Circuit breaker: HALF_OPEN -> OPEN (recovery failed)",
                provider=provider,
            )
            return

        # Increment failure count
        count = self._failure_counts.get(provider, 0) + 1
        self._failure_counts[provider] = count
        self._last_failure_time[provider] = time.time()

        if count >= self.failure_threshold:
            self._states[provider] = CircuitState.OPEN
            logger.warning(
                "Circuit breaker: CLOSED -> OPEN",
                provider=provider,
                failure_count=count,
            )

    def get_state(self, provider: str) -> CircuitState:
        """Get current circuit state for a provider."""
        return self._states.get(provider, CircuitState.CLOSED)

    def get_all_states(self) -> Dict[str, CircuitState]:
        """Get all provider circuit states."""
        return dict(self._states)

    def reset(self, provider: str) -> None:
        """Manually reset a provider's circuit breaker."""
        self._states[provider] = CircuitState.CLOSED
        self._failure_counts[provider] = 0
        self._half_open_calls[provider] = 0
        logger.info("Circuit breaker: manually reset", provider=provider)
