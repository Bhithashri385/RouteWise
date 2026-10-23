# RouteWise — Local AI Gateway

**A lightweight AI gateway for routing requests across local and hosted language models.**

RouteWise is a Python-based AI gateway built using FastAPI and Ollama. It routes chat requests to suitable language models, supports configurable fallback behavior, applies security controls for hosted inference, and tracks request metrics through a monitoring dashboard.

## Overview

RouteWise provides a unified API for interacting with multiple language models through a single gateway. It supports local inference for general and coding tasks, optional hosted-model integration, request validation, error handling, and performance monitoring.

The project focuses on making AI inference easier to manage while maintaining control over privacy, API permissions, and request tracking.

## Key Features

- **Unified API:** Provides a common chat-completions endpoint for model requests.
- **Intelligent Routing:** Routes requests to general-purpose or coding models based on the selected model and task.
- **Local Inference:** Uses Ollama to run language models locally.
- **Hosted Model Support:** Includes configurable DeepSeek API integration.
- **Fallback Handling:** Supports fallback to an alternate local model when enabled.
- **Security Controls:** Blocks sensitive requests from using hosted models and enforces paid-API permissions.
- **Request Validation:** Validates incoming requests and handles invalid inputs.
- **Error Handling:** Handles timeouts, connection failures, and backend HTTP errors.
- **Request Metrics:** Records request status, latency, backend selection, attempts, fallback usage, and token usage where available.
- **Monitoring Dashboard:** Provides a Streamlit dashboard for viewing request metrics.
- **Automated Testing:** Includes gateway tests for routing, validation, permissions, errors, and fallback behavior.

## Architecture

```text
                 Client Application
                         |
                         v
                 FastAPI Gateway
                         |
             Request Validation
                         |
                         v
                Routing and Security
                         |
              +----------+----------+
              |                     |
              v                     v
        Local Inference       Hosted Inference
              |                     |
              v                     v
            Ollama              DeepSeek API
              |                     |
              +----------+----------+
                         |
                         v
                  Model Response
                         |
                         v
                Metrics Recording
                         |
                         v
                 SQLite Database
                         |
                         v
                Streamlit Dashboard
```

Hosted inference is subject to the configured security and permission checks. Paid API access is disabled by default.

## Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| API Framework | FastAPI |
| ASGI Server | Uvicorn |
| Local Model Runtime | Ollama |
| General Model | Qwen 2.5 1.5B |
| Coding Model | Qwen 2.5 Coder 1.5B |
| Hosted Model Integration | DeepSeek API |
| HTTP Client | HTTPX |
| Database | SQLite |
| Dashboard | Streamlit |
| Data Processing | Pandas |
| Testing | Pytest |

## Supported Models

| Model Alias | Purpose |
|---|---|
| `auto` | Selects a model based on the requested task |
| `local` | Uses the default local general model |
| `general` | Handles general-purpose questions |
| `coding` | Handles programming-related questions |
| `deepseek` | Requests hosted inference when permissions allow |

The local models are managed through Ollama. Hosted inference requires a valid API configuration and the necessary permissions.

## Request Routing and Fallback

RouteWise supports automatic task-based routing and explicit model selection.

For example:
- General questions can be routed to Qwen 2.5 1.5B.
- Programming questions can be routed to Qwen 2.5 Coder 1.5B.
- Hosted DeepSeek requests are allowed only when the required security and permission checks pass.

When fallback is enabled, a failed DeepSeek request can fall back to the local general model. Local requests do not automatically fall back to hosted inference.

## Security and Configuration

RouteWise uses environment variables to configure hosted inference.

Create a `.env` file in the project root:

```env
DEEPSEEK_API_KEY=your_actual_api_key
DEEPSEEK_MODEL=deepseek-flash
ENABLE_PAID_APIS=false
```

Replace the placeholder with your own API key if hosted inference is required.

### Security Rules

- Paid API access is disabled by default.
- Hosted requests require server-side permission and request-level permission.
- Requests marked as sensitive are blocked from hosted inference.
- Missing API credentials prevent hosted inference.
- The actual `.env` file must never be committed to GitHub.
- API keys must not be exposed in logs or API responses.

Keep `ENABLE_PAID_APIS=false` unless hosted inference is intentionally enabled after reviewing the provider's pricing and billing requirements.

## Installation and Setup

### Prerequisites

- Python 3.12 or a compatible Python version
- Ollama
- Git
- The required Python dependencies

### 1. Clone the Repository

```bash
git clone https://github.com/Bhithashri385/RouteWise.git
cd RouteWise
```

### 2. Create a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Download the Local Models

```bash
ollama pull qwen2.5:1.5b
ollama pull qwen2.5-coder:1.5b
```

Ensure Ollama is running before sending requests to the local models.

### 5. Configure Environment Variables

Create `.env` using the configuration described in the Security and Configuration section. Keep paid APIs disabled unless needed.

### 6. Start the Gateway

```bash
uvicorn gateway:app --reload
```

The API will be available at:

`http://127.0.0.1:8000`

### 7. Open API Documentation

Visit:

`http://127.0.0.1:8000/docs`

Use the interactive Swagger UI to inspect endpoints and send test requests.

### 8. Start the Monitoring Dashboard

Open a separate terminal, activate the virtual environment, navigate to the project directory, and run:

```bash
streamlit run dashboard.py
```

The dashboard will usually be available at:

`http://localhost:8501`

## API Usage

RouteWise exposes a chat-completions endpoint:

`POST /v1/chat/completions`

Example request for a local general-purpose model:

```json
{
  "model": "general",
  "task": "general",
  "messages": [
    {
      "role": "user",
      "content": "Explain what an API gateway is."
    }
  ],
  "max_tokens": 200,
  "stream": false,
  "allow_fallback": false,
  "sensitive": false,
  "allow_paid": false
}
```

The gateway validates the request, selects the backend, sends the request to the selected model, and returns the model response.

Hosted requests require the additional permissions enforced by the gateway.

## Monitoring and Metrics

RouteWise uses SQLite to persist request metrics and Streamlit to display them.

The monitoring workflow tracks information such as:

- Total requests and failed requests
- Request status codes
- Selected backend and model
- Number of attempted backends
- Whether fallback was used
- Response latency
- Input and output token usage, when available
- Sensitive-request and paid-access permission flags

### Manual Monitoring Verification

1. Start the FastAPI gateway.
2. Open `/docs` and send requests.
3. Refresh the Streamlit dashboard.
4. Verify that request counts, backend information, failures, fallback details, and available token usage reflect the requests.

## Testing

Run the gateway test suite from the project root:

```bash
pytest -q test_gateway.py
```

The current gateway test suite has **11 passing tests**.

The tests cover areas including:
- Gateway health and request validation
- Local model routing
- Hosted inference permission checks
- Sensitive-request blocking
- Backend error handling
- Mocked fallback from DeepSeek to the local general model

Run the Python syntax check with:

```bash
python -m py_compile gateway.py
```

**Testing note:** Automated tests and mocked fallback tests do not confirm that the real DeepSeek service has been contacted successfully. A live DeepSeek API request remains to be verified.

## Project Structure

```text
RouteWise/
├── gateway.py
├── metrics_db.py
├── dashboard.py
├── test_gateway.py
├── README.md
├── requirements.txt
├── .gitignore
└── .venv/
```

The structure above reflects the main files currently identified in the project. Additional files may exist in the repository.

## Current Status and Future Improvements

The project includes a local AI gateway, general and coding model routing, configurable hosted-model integration, request security checks, fallback handling, persistent metrics, and a monitoring dashboard.

The gateway test suite currently passes 11 tests.

Potential future improvements include:
- Verifying a live DeepSeek API request after checking billing and pricing.
- Expanding integration tests for hosted backend responses.
- Improving dashboard visualizations and operational monitoring.
- Adding more detailed performance comparisons between local models.

## License

A license has not yet been specified. Add an appropriate license before distributing the project under explicit open-source terms.
