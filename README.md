# RouteWise — Local AI Gateway

## Overview
RouteWise is a local AI gateway project that connects Python clients to a locally hosted language model. It uses FastAPI to validate incoming chat requests and forwards valid requests to Ollama, which runs the Qwen 2.5 1.5B model.

The gateway provides a single API endpoint for chat completions and handles backend connection failures, timeouts, and server errors.

## Architecture

`Python Client → FastAPI Gateway → Ollama → Qwen 2.5 1.5B → Response`

## Technologies
- Python
- FastAPI
- Uvicorn
- Ollama
- Qwen 2.5 1.5B
- HTTPX
- Requests
- Pytest

## Features
- Runs a local language model through Ollama.
- Exposes a chat completion API.
- Validates request fields, message roles, content, and parameters.
- Maps the client model alias `local` to `qwen2.5:1.5b`.
- Returns backend and request latency information in response headers.
- Handles backend connection failures, timeouts, and server errors.
- Includes automated tests for request validation and backend error handling.
- Provides a Python client for sending prompts through the gateway.

## Requirements
- Python 3
- Ollama
- The `qwen2.5:1.5b` model
- A Python virtual environment

## Setup

Create and activate the virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install fastapi uvicorn httpx pytest requests
```

Download the model if it is not already installed:

```bash
ollama pull qwen2.5:1.5b
```

Ensure the Ollama service is running before sending requests.

## Running the Gateway

From the project directory, start the gateway:

```bash
python -m uvicorn gateway:app --host 127.0.0.1 --port 8000
```

The gateway listens on `127.0.0.1:8000`.

- Health endpoint: `GET /health`
- Interactive API documentation: `http://127.0.0.1:8000/docs`
- Chat completion endpoint: `POST /v1/chat/completions`

## Using the Python Client

Keep the gateway running in one terminal. Open a second terminal and run:

```bash
cd ~/RouteWise
source .venv/bin/activate
python client.py
```

Enter a question when prompted. The client displays the AI response, backend name, and request latency.

## Sample API Request

Send a POST request to `/v1/chat/completions` with this JSON body:

```json
{
  "model": "local",
  "messages": [
    {
      "role": "user",
      "content": "Explain an API gateway in five sentences."
    }
  ],
  "max_tokens": 200,
  "stream": false
}
```

A successful request returns HTTP `200` and a chat completion response. The gateway adds these response headers:

- `X-RouteWise-Backend`
- `X-RouteWise-Latency-Ms`

## Automated Testing

Run the automated gateway tests:

```bash
python -m pytest -v test_gateway.py
```

The test suite covers:
- Health endpoint
- Invalid message role
- Empty message content
- Successful chat request
- Ollama connection failure
- Ollama timeout
- Ollama server error

**Recorded test result:** 7 tests passed. One Starlette deprecation warning was reported by the testing dependencies; it did not cause the tests to fail.

## Manual Validation and Failure Handling

The following results were observed during testing:

| Test case | Observed result |
|---|---|
| Missing `messages` field | HTTP 422 |
| Empty `messages` list | HTTP 422 |
| Unsupported model (`claude`) | HTTP 422 |
| `max_tokens` set to `99999` | HTTP 422 |
| `stream: true` | HTTP 422 |
| Ollama service unavailable | HTTP 503 |
| Request after restarting Ollama | HTTP 200 |

## Example Prompts and Latency

Prompts used during client testing included:

1. Explain an API gateway in five sentences.
2. Explain binary search.
3. Explain a prime-number checking function.

For the first prompt, the recorded client latency was **6098.72 ms (approximately 6.10 seconds)**.

Latency varies with model loading, hardware, prompt length, and system load. Other prompt latency values are not included here because their exact measurements were not recorded in the available evidence.

## Limitations
- Uses one configured local model: `qwen2.5:1.5b`.
- Supports text chat requests only.
- Streaming responses are not supported.
- Does not currently implement multiple backend routing or load balancing.
- Response latency can vary with system and model state.

## Project Structure

- `gateway.py` — FastAPI gateway and request validation.
- `client.py` — Python client for sending requests through the gateway.
- `test_local.py` — Direct local model test script.
- `test_gateway.py` — Automated gateway tests.
- `README.md` — Project documentation.

## Current Status

The gateway, Python client, request validation, backend error handling, and automated test suite have been exercised locally. The project is documented with the observed test results and known limitations.

