
import requests

prompt = input("Ask through RouteWise: ").strip()

if not prompt:
    raise SystemExit("Please enter a question.")

try:
    response = requests.post(
        "http://127.0.0.1:8000/v1/chat/completions",
        json={
            "model": "local",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 200,
            "stream": False,
        },
        timeout=200,
    )
except requests.RequestException as error:
    raise SystemExit(f"Cannot call the gateway: {error}")

if not response.ok:
    raise SystemExit(
        f"Gateway error {response.status_code}: {response.text}"
    )

result = response.json()

print("\nANSWER:")
print(result["choices"][0]["message"]["content"])

print("\nBACKEND:", response.headers.get("X-RouteWise-Backend"))
print("LATENCY:", response.headers.get("X-RouteWise-Latency-Ms"), "ms")
