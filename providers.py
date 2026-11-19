import litellm
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from litellm import acompletion


load_dotenv(Path(__file__).resolve().parent / ".env")


PAID_APIS_ENABLED = (
    os.getenv("ENABLE_PAID_APIS", "false").lower() == "true"
)


@dataclass(frozen=True)
class Backend:
    model: str
    hosted: bool
    on_device: bool = False
    key_env: str | None = None
    api_base: str | None = None


BACKENDS = {
    "general": Backend(
        model="ollama_chat/qwen2.5:1.5b",
        hosted=False,
        on_device=True,
        api_base="http://127.0.0.1:11434",
    ),
    "coding": Backend(
        model="ollama_chat/qwen2.5-coder:1.5b",
        hosted=False,
        on_device=True,
        api_base="http://127.0.0.1:11434",
    ),
    "remote": Backend(
        model=(
            "ollama_chat/"
            + os.getenv("REMOTE_MODEL", "qwen2.5:1.5b").strip()
        ),
        hosted=False,
        on_device=False,
        api_base=os.getenv(
            "REMOTE_BASE",
            "http://127.0.0.1:11435",
        ).strip(),
    ),
    "deepseek": Backend(
        model=f"deepseek/{os.getenv('DEEPSEEK_MODEL', 'deepseek-flash').strip()}",
        hosted=True,
        on_device=False,
        key_env="DEEPSEEK_API_KEY",
    ),
    "claude": Backend(
        model=f"anthropic/{os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-6').strip()}",
        hosted=True,
        on_device=False,
        key_env="ANTHROPIC_API_KEY",
    ),
}


MODELS = {
    alias: backend.model
    for alias, backend in BACKENDS.items()
}


class BackendError(Exception):
    def __init__(self, message, status_code=502):
        super().__init__(message)
        self.status_code = status_code


def validate_access(
    alias: str,
    sensitive: bool = False,
    allow_paid: bool = False,
):
    backend = BACKENDS.get(alias)

    if backend is None:
        raise ValueError(f"Unknown backend: {alias}")

    # Sensitive requests must stay on the laptop.
    if sensitive and not backend.on_device:
        raise PermissionError(
            "Sensitive requests must stay on the laptop."
        )

    # Local and self-hosted cloud models do not require paid API permission.
    if not backend.hosted:
        return backend

    # Hosted APIs require both server and request permission.
    if not PAID_APIS_ENABLED or not allow_paid:
        raise PermissionError(
            "Paid API use requires server and request permission."
        )

    if (
        not MODELS[alias]
        or not os.getenv(backend.key_env or "", "").strip()
    ):
        raise PermissionError(
            "The selected hosted backend is not configured."
        )

    return backend


async def complete(
    alias: str,
    messages: list[dict],
    max_tokens: int,
    sensitive: bool = False,
    allow_paid: bool = False,
) -> dict:

    backend = validate_access(
        alias,
        sensitive=sensitive,
        allow_paid=allow_paid,
    )

    api_key = (
        os.getenv(backend.key_env, "").strip()
        if backend.key_env
        else None
    )

    try:
        response = await acompletion(
            model=backend.model,
            messages=messages,
            max_tokens=max_tokens,
            api_key=api_key,
            api_base=backend.api_base,
        )

        return response.model_dump()

    except Exception as exc:
        import httpx

        if isinstance(exc, httpx.TimeoutException):
            status_code = 504
        elif isinstance(exc, httpx.HTTPStatusError):
            status_code = 502
        elif isinstance(exc, (httpx.RequestError, litellm.APIConnectionError)):
            status_code = 503
        else:
            status_code = 502

        raise BackendError(
            f"{alias} provider failed: {exc}",
            status_code=status_code,
        ) from exc
