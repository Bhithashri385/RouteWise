import os
from pathlib import Path
from dotenv import load_dotenv
import asyncio
import logging
import time
import uuid
from providers import BACKENDS, MODELS, complete, validate_access
from datetime import datetime, timezone
from typing import Literal

import httpx
from fastapi import FastAPI, HTTPException, Request as HTTPRequest, Response
from pydantic import BaseModel, ConfigDict, Field

from metrics_db import save_request

app = FastAPI(title="RouteWise — Day 3")

logger = logging.getLogger("routewise")


@app.middleware("http")
async def track_request(request: HTTPRequest, call_next):
    if request.url.path != "/v1/chat/completions":
        return await call_next(request)

    request_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    started = time.perf_counter()
    status_code = 500

    request.state.metrics = {}

    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-RouteWise-Request-Id"] = request_id
        return response

    finally:
        latency_ms = round(
            (time.perf_counter() - started) * 1000,
            2,
        )

        try:
            await asyncio.to_thread(
                save_request,
                request_id,
                timestamp,
                status_code,
                latency_ms,
                dict(request.state.metrics),
            )
        except Exception:
            logger.exception(
                "Failed to save metrics for request %s",
                request_id,
            )

class Message(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model: Literal["auto", "local", "general", "coding", "deepseek", "claude"] = "auto"
    task: Literal["general", "coding"] = "general"
    messages: list[Message] = Field(min_length=1, max_length=10)
    max_tokens: int = Field(default=256, ge=1, le=512)
    stream: Literal[False] = False
    allow_fallback: bool = False
    sensitive: bool = False
    allow_paid: bool = False

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
    http_request: HTTPRequest,
):
    # Select the primary model.
    if request.model in ("deepseek", "claude"):
        selected = request.model
        reason = "explicit hosted model selection"

        try:
            validate_access(
                selected,
                request.sensitive,
                request.allow_paid,
            )
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc))

    elif request.model in ("general", "coding"):
        selected = request.model
        reason = "explicit model selection"

    elif request.model == "local":
        selected = "general"
        reason = "local alias maps to general model"

    else:
        selected = request.task
        reason = f"automatic routing based on task: {request.task}"

    http_request.state.metrics.update({
        "requested_model": request.model,
        "task": request.task,
        "reason": reason,
        "attempts": [],
        "backend": None,
        "fallback_used": False,
        "input_tokens": None,
        "output_tokens": None,
        "sensitive": request.sensitive,
        "allow_paid": request.allow_paid,
    })

    # Prepare fallback order.
    attempts = [selected]

    if request.allow_fallback:
        if selected in ("deepseek", "claude"):
            attempts.append("general")
        else:
            alternate = "coding" if selected == "general" else "general"
            attempts.append(alternate)

    started = time.perf_counter()
    last_error = "Provider request failed"
    last_status = 503
    attempted_models = []

    payload = {
        "messages": [
            message.model_dump()
            for message in request.messages
        ],
        "max_tokens": request.max_tokens,
        "stream": False,
    }

    for model_key in attempts:
        attempted_models.append(model_key)

        http_request.state.metrics["attempts"] = attempted_models.copy()
        http_request.state.metrics["fallback_used"] = model_key != selected

        try:
            result = await complete(
                alias=model_key,
                payload=payload,
                sensitive=request.sensitive,
                allow_paid=request.allow_paid,
            )

            latency_ms = round(
                (time.perf_counter() - started) * 1000,
                2,
            )

            response.headers["X-RouteWise-Backend"] = model_key
            response.headers["X-RouteWise-Model"] = BACKENDS[model_key].model
            response.headers["X-RouteWise-Reason"] = reason
            response.headers["X-RouteWise-Attempts"] = ",".join(attempted_models)
            response.headers["X-RouteWise-Fallback"] = str(
                model_key != selected
            ).lower()
            response.headers["X-RouteWise-Latency-Ms"] = str(latency_ms)

            usage = result.get("usage") or {}

            http_request.state.metrics.update({
                "backend": model_key,
                "input_tokens": usage.get("prompt_tokens"),
                "output_tokens": usage.get("completion_tokens"),
            })

            return result

        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc))

        except httpx.TimeoutException as exc:
            last_error = f"{model_key} request timed out: {exc}"
            last_status = 504

        except httpx.HTTPStatusError as exc:
            last_error = f"{model_key} returned an HTTP error: {exc}"
            last_status = 502

        except httpx.RequestError as exc:
            last_error = f"Could not connect to {model_key}: {exc}"
            last_status = 503

        except Exception as exc:
            last_error = f"{model_key} provider failed: {exc}"
            last_status = 502

    raise HTTPException(
        status_code=last_status,
        detail={
            "error": last_error,
            "attempts": attempted_models,
        },
    )
