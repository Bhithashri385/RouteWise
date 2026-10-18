# RouteWise — Local AI Gateway

A lightweight local AI gateway built with Python, FastAPI, and Ollama to route chat requests between multiple locally running language models.

## Overview

RouteWise provides a single API endpoint for interacting with multiple local language models. It supports explicit model selection, task-based routing, optional fallback, request validation, and routing metadata.

## Architecture

```text
Python Client
     |
     v
FastAPI Gateway
     |
     v
Request Validation
     |
     v
Model Routing
     |
     +----------------------+
     |                      |
     v                      v
General Model           Coding Model
Qwen 2.5 1.5B           Qwen 2.5 Coder 1.5B
     |                      |
     +----------+-----------+
                |
                v
           Ollama Runtime
                |
                v
             Response
```

## Technology Stack

- Python
- FastAPI
- Uvicorn
- Ollama
- Qwen 2.5 1.5B
- Qwen 2.5 Coder 1.5B
- HTTPX
- Requests
- Pytest

## Features

- Unified chat-completion API.
- Local language model inference through Ollama.
- Two configured model aliases: `general` and `coding`.
- Task-based automatic routing using the task category supplied by the client.
- Explicit model selection.
- Backward compatibility with the `local` alias.
- Optional fallback to the alternate configured model.
- Request validation for messages, roles, content, and parameters.
- Response headers containing routing information and latency.
- Error handling for backend connection failures, timeouts, and server errors.
- Python client and automated gateway tests.

## Model Configuration

| Alias | Model | Purpose |
|---|---|---|
| `general` | `qwen2.5:1.5b` | General-purpose queries |
| `coding` | `qwen2.5-coder:1.5b` | Programming and coding tasks |
| `local` | Existing compatibility alias | Preserves earlier client behavior |

## Requirements

- Python 3
- Ollama
- Required Qwen models
- Python virtual environment
- Project dependencies

## Installation

### 1. Navigate to the Project

```bash
cd ~/RouteWise
```

### 2. Activate the Virtual Environment

```bash
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Download the Models

```bash
ollama pull qwen2.5:1.5b
ollama pull qwen2.5-coder:1.5b
```

Verify the installed models:

```bash
ollama list
```

Ensure that the Ollama service is running before starting the gateway.

## Running the Gateway

Start the FastAPI application using the actual module and application object defined in the project.

For example, if `gateway.py` contains an application object named `app`:

```bash
uvicorn gateway:app --host 127.0.0.1 --port 8000
```

Local gateway address:

```text
http://127.0.0.1:8000
```

## API Usage

Example general-purpose request:

```json
{
  "model": "general",
  "task": "general",
  "messages": [
    {
      "role": "user",
      "content": "Explain how an API gateway works."
    }
  ]
}
```

Example coding request:

```json
{
  "model": "coding",
  "task": "coding",
  "messages": [
    {
      "role": "user",
      "content": "Write a Python function to check whether a string is a palindrome."
    }
  ]
}
```

Use the endpoint and request fields supported by the actual implementation.

## Model Routing and Fallback

RouteWise supports:

- **Explicit routing:** Select a configured model using its alias.
- **Task-based routing:** Select a model according to the task category supplied by the client.
- **Fallback:** Attempt the alternate configured model when enabled and an applicable failure occurs.

The `local` alias is maintained for compatibility with the earlier client.

## Response Metadata

The gateway provides routing information through response headers, including:

- Selected model.
- Routing reason.
- Models attempted.
- Fallback status.
- Request latency.

This information helps with debugging and evaluating gateway behavior.

## Testing

Run the automated tests using Pytest:

```bash
pytest
```

Key testing scenarios include:

- General and coding model requests.
- Explicit model selection.
- Task-based routing.
- Alias compatibility.
- Fallback behavior.
- Request validation.
- Backend errors and timeouts.
- Response metadata.

