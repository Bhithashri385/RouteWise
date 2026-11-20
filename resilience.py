
import time


class CircuitUnavailable(Exception):
    """Raised when a backend circuit is not accepting requests."""
    pass


class CircuitBreaker:

    def __init__(self, threshold=3, cooldown=30, clock=None):
        self.threshold = threshold
        self.cooldown = cooldown
        self.clock = clock or time.monotonic

        self.state = "closed"
        self.failures = 0
        self.retry_at = 0.0
        self.generation = 0

    def admit(self):
        now = self.clock()

        if self.state == "open":
            if now < self.retry_at:
                raise CircuitUnavailable()

            self.state = "half_open"

        elif self.state == "half_open":
            raise CircuitUnavailable()

        return self.generation

    def finish(self, token, success):

        if token != self.generation:
            return

        if self.state == "open":
            return

        if success:
            self.state = "closed"
            self.failures = 0
            self.retry_at = 0.0
            self.generation += 1

        else:
            self.failures += 1

            if self.state == "half_open" or self.failures >= self.threshold:
                self.state = "open"
                self.retry_at = self.clock() + self.cooldown
                self.generation += 1

    def snapshot(self):
        now = self.clock()

        return {
            "state": self.state,
            "failures": self.failures,
            "retry_after_seconds": max(
                0,
                round(self.retry_at - now, 2)
            ),
        }
