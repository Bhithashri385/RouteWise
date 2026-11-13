import time
import requests

prompt = input("Ask the local model: ").strip()

if not prompt:
    raise SystemExit("Please enter a question.")

started = time.perf_counter()

try:
    response = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": "qwen2.5:1.5b",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "options": {"num_predict": 200},
        },
        timeout=180,
    )
    response.raise_for_status()
    result = response.json()

except requests.RequestException as error:
    raise SystemExit(f"Request failed: {error}")

elapsed = time.perf_counter() - started
message = result["message"]["content"]
tokens = result.get("eval_count", 0)

print("\nMODEL RESPONSE:")
print(message)
print(f"\nElapsed time: {elapsed:.2f} seconds")
print(f"Generated tokens: {tokens}")
