
from resilience import CircuitBreaker, CircuitUnavailable


def expect_blocked(circuit):
    try:
        circuit.admit()
    except CircuitUnavailable:
        return

    raise AssertionError("Expected circuit to block request")


now = [0.0]

circuit = CircuitBreaker(
    threshold=3,
    cooldown=30,
    clock=lambda: now[0],
)

for _ in range(3):
    token = circuit.admit()
    circuit.finish(token, False)

assert circuit.state == "open"

expect_blocked(circuit)

now[0] = 31.0

probe = circuit.admit()

assert circuit.state == "half_open"

expect_blocked(circuit)

circuit.finish(probe, True)

assert circuit.state == "closed"

print("Circuit transition checks passed.")



# Test failed recovery starts a fresh cooldown.
now[0] = 0.0

recovery = CircuitBreaker(
    threshold=3,
    cooldown=30,
    clock=lambda: now[0],
)

for _ in range(3):
    token = recovery.admit()
    recovery.finish(token, False)

now[0] = 31.0

probe = recovery.admit()
assert recovery.state == "half_open"

recovery.finish(probe, False)

assert recovery.state == "open"
assert recovery.failures == 4
assert recovery.snapshot()["retry_after_seconds"] == 30

expect_blocked(recovery)

print("Recovery failure and cooldown checks passed.")
