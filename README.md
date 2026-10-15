k# RouteWise

## Overview
RouteWise demonstrates how to run a local AI model using Ollama and access it through Python. It also includes a FastAPI gateway that validates requests and forwards them to the local model.

## Model and Technologies
- Qwen 2.5 1.5B
- Ollama
- Python
- FastAPI
- Uvicorn
- HTTPX
- Pytest

## Architecture
Client → FastAPI Gateway → Ollama → Qwen Model → Response

## Features
- Sends prompts to a local AI model.
- Measures response time and records generated token counts in the model test script.
- Provides an API endpoint for chat completions.
- Validates message roles, content, and request parameters.
- Maps the client model alias `local` to `qwen2.5:1.5b`.
- Handles backend connection failures, timeouts, and server errors.
- Includes automated tests for request validation and error handling.

## Requirements
- Python 3
- Ollama
- `qwen2.5:1.5b`
- FastAPI
- Uvicorn
- HTTPX
- Pytest
- Requests

## Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the required packages:

```bash
python -m pip install fastapi uvicorn httpx pytest requests
```

Download the model if it is not already installed:

```bash
ollama pull qwen2.5:1.5b
```

Make sure Ollama is running before sending chat requests.

## Running the Model Test Script

```bash
python test_local.py
```

## Running the Gateway

Start the gateway from the project directory:

```bash
python -m uvicorn gateway:app --host 127.0.0.1 --port 8000
```

Interactive API documentation:

http://127.0.0.1:8000/docs

Health endpoint:

http://127.0.0.1:8000/health

Chat endpoint: `POST /v1/chat/completions`

The gateway accepts the client model alias `local` and forwards chat requests to the configured Ollama model.

## Automated Testing

Run the gateway tests with:

```bash
python -m pytest -v test_gateway.py
```

The test suite checks:
- Health endpoint response
- Invalid role validation
- Empty message validation
- Successful chat requests
- Ollama connection failure (`503`)
- Ollama timeout (`504`)
- Ollama server error (`502`)

Seven automated tests have passed in the current development run. A Starlette deprecation warning was also reported by the testing dependencies.

## Project Structure
- `test_local.py` — Tests direct access to the local model.
- `gateway.py` — Implements the FastAPI gateway.
- `test_gateway.py` — Contains automated gateway tests.
- `README.md` — Project documentation.
