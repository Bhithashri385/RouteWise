import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import FastAPI, HTTPException, Request as HTTPRequest, Response
from pydantic import BaseModel, ConfigDict, Field

from providers import (
    BACKENDS,
    MODELS,
    BackendError,
    CircuitOpenError,
    complete,
    validate_access,
)
from metrics_db import save_request
from readiness import backend_status

app = FastAPI(title="RouteWise — Day 7")

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

    model: Literal[
        "auto",
        "local",
        "general",
        "coding",
        "deepseek",
        "claude",
        "remote",
    ] = "auto"
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



@app.get("/backends")
async def backends():
    return {"backends": await backend_status()}


def select_routes(request: ChatRequest):
    if request.model in BACKENDS:
        selected = request.model
        reason = "explicit model selection"

    elif request.model == "local":
        selected = "general"
        reason = "local alias maps to general"

    else:
        selected = request.task
        reason = f"local task routing: {request.task}"

    validate_access(
        selected,
        sensitive=request.sensitive,
        allow_paid=request.allow_paid,
    )

    routes = [selected]

    if request.allow_fallback:
        if not BACKENDS[selected].on_device:
            routes.append("general")
        else:
            alternate = (
                "coding" if selected == "general" else "general"
            )
            routes.append(alternate)

    if request.sensitive:
        reason = f"laptop-only privacy policy; {reason}"

    return routes, reason
@app.post("/v1/chat/completions")
async def chat_completions(
    request: ChatRequest,
    response: Response,
    http_request: HTTPRequest,
):
    # Select permitted routes.
    try:
        routes, reason = select_routes(request)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))

    selected = routes[0]
    attempts = routes

    # Initialize request metrics.
    http_request.state.metrics.update({
        "requested_model": request.model,
        "task": request.task,
        "reason": reason,
        "attempts": [],
        "skipped": [],
        "backend": None,
        "fallback_used": False,
        "input_tokens": None,
        "output_tokens": None,
        "sensitive": request.sensitive,
        "allow_paid": request.allow_paid,
        "location": None,
    })

    started = time.perf_counter()
    last_error = "Provider request failed"
    last_status = 503
    attempted_models = []
    # Try each permitted backend.
    for route_index, model_key in enumerate(attempts):
        attempted_models.append(model_key)

        http_request.state.metrics["attempts"] = (
            attempted_models.copy()
        )
        http_request.state.metrics["fallback_used"] = (
            model_key != selected
        )

        try:
            result = await complete(
                alias=model_key,
                messages=[
                    message.model_dump()
                    for message in request.messages
                ],
                max_tokens=request.max_tokens,
                sensitive=request.sensitive,
                allow_paid=request.allow_paid,
            )

            # Successful response.
            latency_ms = round(
                (time.perf_counter() - started) * 1000,
                2,
            )

            backend = BACKENDS[model_key]

            location = (
                "laptop" if backend.on_device
                else "provider_api" if backend.hosted
                else "cloud_vm"
            )
            # Response headers.
            response.headers["X-RouteWise-Backend"] = model_key
            response.headers["X-RouteWise-Model"] = (
                BACKENDS[model_key].model
            )
            response.headers["X-RouteWise-Reason"] = reason
            response.headers["X-RouteWise-Attempts"] = (
                ",".join(attempted_models)
            )
            response.headers["X-RouteWise-Fallback"] = str(
                route_index > 0
            ).lower()
            response.headers["X-RouteWise-Skipped"] = ",".join(
                http_request.state.metrics["skipped"]
            )
            response.headers["X-RouteWise-Latency-Ms"] = str(
                latency_ms
            )
            response.headers["X-RouteWise-Location"] = location

            # Extract token usage.
            usage = result.get("usage") or {}

            http_request.state.metrics.update({
                "backend": model_key,
                "actual_model": MODELS[model_key],
                "input_tokens": usage.get("prompt_tokens"),
                "output_tokens": usage.get("completion_tokens"),
                "location": location,
            })
            return result

        except PermissionError as exc:
            raise HTTPException(
                status_code=403,
                detail=str(exc),
            )

        except CircuitOpenError:
            # Remove this backend because no provider call happened.
            attempted_models.pop()
            http_request.state.metrics["attempts"] = (
                attempted_models.copy()
            )
            http_request.state.metrics["skipped"].append(
                model_key
            )
            continue

        except BackendError as exc:
            last_error = str(exc)
            last_status = exc.status_code
            continue
        except Exception as exc:
            last_error = f"{model_key} provider failed: {exc}"
            continue

    # All permitted backends failed.
    raise HTTPException(
        status_code=last_status,
        detail={
            "error": last_error,
            "attempts": attempted_models,
        },
    )
