import time
from typing import Literal

import httpx
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field

app = FastAPI(title="RouteWise Gateway")

OLLAMA_URL = "http://127.0.0.1:11434/v1/chat/completions"
LOCAL_MODEL = "qwen2.5:1.5b"


class Message(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1, max_length=6000)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model: Literal["local"] = "local"
    messages: list[Message] = Field(min_length=1, max_length=10)
    max_tokens: int = Field(default=200, ge=1, le=512)
    stream: Literal[False] = False


@app.get("/health")
def health():
    return {
        "gateway": "running",
        "configured_backend": "ollama",
        "configured_model": LOCAL_MODEL,
    }


@app.post("/v1/chat/completions")
async def chat(request: ChatRequest, response: Response):
    started = time.perf_counter()

    payload = {
        "model": LOCAL_MODEL,
        "messages": [message.model_dump() for message in request.messages],
        "max_tokens": request.max_tokens,
        "stream": False,
    }

    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            backend_response = await client.post(OLLAMA_URL, json=payload)
            backend_response.raise_for_status()
            result = backend_response.json()
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="Ollama is unavailable. Please start Ollama and retry.",
        )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Ollama request timed out.")
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=502, detail="Ollama returned an error.")
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Could not communicate with Ollama.")

    elapsed_ms = (time.perf_counter() - started) * 1000
    response.headers["X-RouteWise-Backend"] = "local"
    response.headers["X-RouteWise-Latency-Ms"] = f"{elapsed_ms:.2f}"

    return result
