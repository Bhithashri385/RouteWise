# RouteWise — Local AI Gateway

RouteWise is a small local AI gateway built with Python, FastAPI, and Ollama. It provides one API endpoint to interact with different local AI models and routes requests based on the selected model or task.

The project also includes an optional fallback mechanism and a monitoring dashboard to track requests, failures, response times, and model usage.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [Model Configuration](#model-configuration)
- [Requirements](#requirements)
- [Installation](#installation)
- [Running the Gateway](#running-the-gateway)
- [Using the API](#using-the-api)
- [Monitoring Dashboard](#monitoring-dashboard)
- [Understanding the Metrics](#understanding-the-metrics)
- [Privacy](#privacy)
- [Testing](#testing)
- [Project Structure](#project-structure)

## Overview

When working with multiple AI models, it can be inconvenient to manage a separate API for each model. RouteWise solves this by providing a single gateway that forwards requests to the appropriate local model.

For example, general questions can be sent to the general-purpose model, while programming questions can be sent to the coding model.

If the selected model fails and fallback is enabled, RouteWise can try the alternate model. The monitoring dashboard helps track how these requests perform.

## Features

- One API endpoint for chat-completion requests.
- Local AI inference using Ollama.
- Separate general-purpose and coding models.
- Automatic routing based on the requested task.
- Explicit model selection.
- Support for the existing `local` model alias.
- Optional fallback to an alternate model.
- Request validation and backend error handling.
- Response headers containing routing and latency information.
- SQLite-based request metrics storage.
- Interactive dashboard for monitoring requests and failures.
- Response-time statistics and successful requests grouped by model.
- Token usage tracking when Ollama reports it.

## Technology Stack

- **Python** — Main programming language.
- **FastAPI** — Builds the API gateway.
- **Uvicorn** — Runs the gateway server.
- **Ollama** — Runs AI models locally.
- **Qwen 2.5 1.5B** — General-purpose model.
- **Qwen 2.5 Coder 1.5B** — Coding model.
- **HTTPX** — Sends requests to Ollama.
- **SQLite** — Stores request metrics.
- **Streamlit** — Builds the monitoring dashboard.
- **Pandas** — Organizes metrics for display.
- **Pytest** — Runs automated tests.

## Architecture

```text
Client
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
  +--------------------------+
  |                          |
  v                          v
General Model             Coding Model
  |                          |
  +------------+-------------+
               |
               v
        Ollama Runtime
               |
               v
         API Response

Gateway Request Metrics
               |
               v
         SQLite Database
               |
               v
       Streamlit Dashboard
```

The gateway handles incoming requests, selects the appropriate model, and returns the model response. Request metadata is stored separately in SQLite and displayed through the dashboard.

## Model Configuration

| Alias | Ollama model | Purpose |
|---|---|---|
| `general` | `qwen2.5:1.5b` | General questions and everyday tasks |
| `coding` | `qwen2.5-coder:1.5b` | Programming and coding tasks |
| `local` | Maps to the general model | Compatibility with the earlier client |

## Requirements

Before running the project, make sure you have:

- Python 3 installed.
- Ollama installed and running.
- The required Qwen models downloaded.
- A Python virtual environment.
- The project dependencies installed.

## Installation

### 1. Open the project directory

```bash
cd ~/RouteWise
```

### 2. Activate the virtual environment

```bash
source .venv/bin/activate
```

### 3. Install the dependencies

```bash
python -m pip install -r requirements.txt
```

If you are setting up the Day 4 dashboard and Streamlit or Pandas are not already included in your requirements, install them using:

```bash
python -m pip install streamlit pandas
```

### 4. Download the required models

```bash
ollama pull qwen2.5:1.5b
ollama pull qwen2.5-coder:1.5b
```

Check the installed models:

```bash
ollama list
```

Make sure both models are available before testing normal routing and fallback.

## Running the Gateway

Open a terminal in the project directory and run:

```bash
cd ~/RouteWise
source .venv/bin/activate
python -m uvicorn gateway:app --host 127.0.0.1 --port 8000 --reload
```

The gateway runs locally at:

**http://localhost:8000**

To explore and test the API, open:

**http://localhost:8000/docs**

Keep the terminal open while using the gateway.

## Using the API

RouteWise exposes the following chat-completion endpoint:

`POST /v1/chat/completions`

### Example: General request

```json
{
  "model": "general",
  "task": "general",
  "messages": [
    {
      "role": "user",
      "content": "Explain how an API gateway works."
    }
  ],
  "max_tokens": 100,
  "stream": false,
  "allow_fallback": false
}
```

### Example: Coding request

```json
{
  "model": "coding",
  "task": "coding",
  "messages": [
    {
      "role": "user",
      "content": "Write a Python function to check whether a string is a palindrome."
    }
  ],
  "max_tokens": 100,
  "stream": false,
  "allow_fallback": false
}
```

You can send these requests through the API documentation page at `http://localhost:8000/docs`.

### Model routing and fallback

RouteWise supports explicit model selection and task-based routing.

When fallback is enabled, the gateway can try the alternate configured model if the first model attempt fails. If the alternate model also fails, the gateway returns an error.

The response headers include routing information such as:

- `X-RouteWise-Backend`
- `X-RouteWise-Model`
- `X-RouteWise-Reason`
- `X-RouteWise-Attempts`
- `X-RouteWise-Fallback`
- `X-RouteWise-Latency-Ms`
- `X-RouteWise-Request-Id`

These headers help explain how each request was handled.

## Monitoring Dashboard

RouteWise includes a Streamlit dashboard that displays request metrics stored in the local SQLite database.

### Start the dashboard

Open a second terminal. Keep the gateway running in the first terminal.

```bash
cd ~/RouteWise
source .venv/bin/activate
python -m streamlit run dashboard.py --server.address 0.0.0.0 --server.port 8501
```

Open the dashboard at:

**http://localhost:8501**

After sending requests through the gateway, click **Refresh** to reload the metrics.

### Dashboard features

- Total number of requests.
- Successful and failed request counts.
- Requests that used fallback.
- Successful requests grouped by backend model.
- Average, median, and 95th-percentile response times.
- Reported input and output token totals.
- A table of recent requests with routing metadata.

The dashboard uses `routewise.db`, which is created locally by the metrics module.

## Understanding the Metrics

- **Total requests:** Number of completed gateway requests recorded in the database.
- **Successful requests:** Requests that return an HTTP status code from 200 to 299.
- **Failed requests:** Requests that return a status code outside that range, including validation errors.
- **Successful requests by model:** Number of successful gateway requests handled by each backend model.
- **Response time:** Time spent handling the request, including model attempts and gateway processing.
- **Fallback request:** A request where the gateway attempts an alternate model after the initial model fails. A successful fallback still counts as one client request.
- **Token usage:** Input and output token counts reported by Ollama for successful responses. If a count is missing, it remains unknown rather than being treated as zero.

Response-time statistics are more useful when collected over a larger number of requests. A small sample may not represent normal performance.

## Privacy

RouteWise does not store prompts or model answers in its metrics database.

The database stores request identifiers, timestamps, HTTP status codes, latency, and approved routing metadata, such as the requested model, backend, model attempts, fallback status, and reported token counts.

The local database files are excluded from Git to avoid uploading local request metrics.

## Testing

Run the automated tests from the project directory:

```bash
cd ~/RouteWise
source .venv/bin/activate
pytest -v
```

The tests should cover supported routing behavior, model selection, fallback, request validation, backend errors, and response metadata.

The monitoring workflow should also be checked manually by sending requests through `/docs` and refreshing the dashboard.

## Project Structure

```text
RouteWise/
├── gateway.py
├── metrics_db.py
├── dashboard.py
├── README.md
├── requirements.txt
├── .gitignore
└── tests/
```

The exact test filenames may differ depending on the current project setup.

## Current Status

RouteWise has a working local gateway and a request-monitoring dashboard. The dashboard tracks request counts, failures, model routing, response times, fallback activity, and reported token usage.

The project is being developed incrementally, with testing and improvements added as new features are introduced.
