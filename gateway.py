import time
from typing import Literal

import httpx
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI(title="RouteWise — Day 3")

OLLAMA_URL = "http://127.0.0.1:11434/v1/chat/completions"

MODELS = {
    "general": "qwen2.5:1.5b",
    "coding": "qwen2.5-coder:1.5b",
}


class Message(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: Literal["auto", "local", "general", "coding"] = "auto"
    task: Literal["general", "coding"] = "general"
    messages: list[Message] = Field(min_length=1, max_length=10)
    max_tokens: int = Field(default=256, ge=1, le=512)
    stream: Literal[False] = False
    allow_fallback: bool = False


@app.get("/health")
async def health():
    return {
        "gateway": "running",
        "status": "ok",
        "models": MODELS,
    }


@app.post("/v1/chat/completions")
async def chat_completions(
    request: ChatRequest,
    response: Response,
):
    # Select the primary model.
    if request.model in ("general", "coding"):
        selected = request.model
        reason = "explicit model selection"
    elif request.model == "local":
        selected = "general"
        reason = "local alias maps to general model"
    else:
        selected = request.task
        reason = f"automatic routing based on task: {request.task}"

    # Prepare the attempt order.
    attempts = [selected]

    if request.allow_fallback:
        alternate = "coding" if selected == "general" else "general"
        attempts.append(alternate)

    started = time.perf_counter()
    last_error = "Ollama request failed"
    last_status = 503
    attempted_models = []

    async with httpx.AsyncClient(timeout=120.0) as client:
        for model_key in attempts:
            ollama_model = MODELS[model_key]
            attempted_models.append(model_key)

            payload = {
                "model": ollama_model,
                "messages": [
                    message.model_dump()
                    for message in request.messages
                ],
                "max_tokens": request.max_tokens,
                "stream": False,
            }

            try:
                result = await client.post(
                    OLLAMA_URL,
                    json=payload,
                )
                result.raise_for_status()

                latency_ms = round(
                    (time.perf_counter() - started) * 1000,
                    2,
                )

                response.headers["X-RouteWise-Backend"] = model_key
                response.headers["X-RouteWise-Model"] = ollama_model
                response.headers["X-RouteWise-Reason"] = reason
                response.headers["X-RouteWise-Attempts"] = ",".join(
                    attempted_models
                )
                response.headers["X-RouteWise-Fallback"] = str(
                    model_key != selected
                ).lower()
                response.headers["X-RouteWise-Latency-Ms"] = str(
                    latency_ms
                )

                return result.json()

            except httpx.TimeoutException:
                last_error = "Ollama request timed out"
                last_status = 504

            except httpx.HTTPStatusError as exc:
                last_error = f"Ollama returned an HTTP error: {exc}"
                last_status = 502

            except httpx.RequestError as exc:
                last_error = f"Could not connect to Ollama: {exc}"
                last_status = 503

    raise HTTPException(
        status_code=last_status,
        detail={
            "error": last_error,
            "attempts": attempted_models,
        },
    )
