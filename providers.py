from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")


@dataclass
class Backend:
    name: str
    provider: str
    model: str
    requires_paid: bool = False


BACKENDS = {
    "general": Backend(
        name="general",
        provider="ollama",
        model="qwen2.5:1.5b",
    ),
    "coding": Backend(
        name="coding",
        provider="ollama",
        model="qwen2.5-coder:1.5b",
    ),
    "deepseek": Backend(
        name="deepseek",
        provider="deepseek",
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-flash").strip(),
        requires_paid=True,
    ),
    "claude": Backend(
        name="claude",
        provider="anthropic",
        model=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6").strip(),
        requires_paid=True,
    ),
}

MODELS = {
    alias: backend.model
    for alias, backend in BACKENDS.items()
}

OLLAMA_URL = "http://127.0.0.1:11434"
PAID_APIS_ENABLED = (
    os.getenv("ENABLE_PAID_APIS", "false").lower() == "true"
)


def validate_access(alias: str, sensitive: bool, allow_paid: bool):
    backend = BACKENDS.get(alias)

    if backend is None:
        raise ValueError(f"Unknown backend: {alias}")

    if backend.requires_paid:
        if sensitive:
            raise PermissionError(
                "Sensitive requests cannot use hosted models."
            )

        if not PAID_APIS_ENABLED or not allow_paid:
            raise PermissionError(
                "Paid API use requires server and request permission."
            )

        if alias == "deepseek" and not os.getenv("DEEPSEEK_API_KEY", "").strip():
            raise PermissionError("DeepSeek API key is not configured.")

        if alias == "claude" and not os.getenv("ANTHROPIC_API_KEY", "").strip():
            raise PermissionError("Anthropic API key is not configured.")

    return backend
async def complete(
    alias: str,
    payload: dict,
    sensitive: bool = False,
    allow_paid: bool = False,
) -> dict:
    backend = validate_access(alias, sensitive, allow_paid)

    if backend.provider == "ollama":
        import httpx

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{OLLAMA_URL}/v1/chat/completions",
                json={**payload, "model": backend.model},
            )
            response.raise_for_status()
            return response.json()

    from litellm import acompletion

    if backend.provider == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        model = f"deepseek/{backend.model}"

    elif backend.provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        model = f"anthropic/{backend.model}"

    else:
        raise ValueError(f"Unsupported provider: {backend.provider}")

    response = await acompletion(
        model=model,
        messages=payload["messages"],
        max_tokens=payload.get("max_tokens", 256),
        api_key=api_key,
    )

    return response.model_dump()
