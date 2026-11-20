import asyncio
import os

import httpx

from providers import BACKENDS, CIRCUITS, MODELS


async def inspect_backend(alias, backend, client):
    row = {
        "alias": alias,
        "model": MODELS[alias],
        "location": (
            "laptop" if backend.on_device
            else "provider_api" if backend.hosted
            else "cloud_vm"
        ),
        **CIRCUITS[alias].snapshot(),
    }

    # Hosted providers: check configuration only.
    if backend.hosted:
        configured = bool(
            MODELS[alias]
            and os.getenv(backend.key_env or "", "").strip()
        )

        row["readiness"] = (
            "configured_unverified" if configured
            else "not_configured"
        )
        return row

    # Local and self-hosted Ollama backends.
    try:
        url = backend.api_base.rstrip("/") + "/api/tags"

        response = await client.get(url)
        response.raise_for_status()

        installed_models = [
            item["name"]
            for item in response.json().get("models", [])
        ]

        expected_model = backend.model.split("/", 1)[-1]

        installed = expected_model in installed_models

        row["readiness"] = (
            "ready" if installed else "model_missing"
        )

        row["model_installed"] = installed

    except (httpx.HTTPError, ValueError, KeyError):
        row["readiness"] = "unreachable"
        row["model_installed"] = False

    return row


async def backend_status():
    async with httpx.AsyncClient(timeout=5.0) as client:
        results = await asyncio.gather(
            *[
                inspect_backend(alias, backend, client)
                for alias, backend in BACKENDS.items()
            ]
        )

    return results
