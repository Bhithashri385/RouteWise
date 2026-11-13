# RouteWise — Local AI Gateway

A lightweight AI gateway for routing requests across local and hosted language models.

RouteWise is a Python-based AI gateway built with FastAPI that provides a unified interface for interacting with multiple AI models. It routes requests to suitable models, manages provider communication, enforces privacy and paid API restrictions, handles failures through fallback mechanisms, and monitors performance through a dashboard.

The goal of RouteWise is to make multiple AI models accessible through a single gateway while maintaining control over model selection, privacy, cost, and performance.

## Key Features

- **Unified API:** Provides a single API endpoint for interacting with multiple AI models.
- **Model Routing:** Routes requests to general-purpose, coding, or explicitly selected models.
- **Local AI Inference:** Runs models locally using Ollama.
- **Hosted AI Integration:** Supports DeepSeek and Anthropic Claude through LiteLLM.
- **Privacy Protection:** Prevents sensitive requests from being sent to hosted providers.
- **Paid API Controls:** Requires both operator-level and request-level permission before using paid hosted models.
- **Fallback Mechanism:** Can switch to a local model when a hosted model fails.
- **Request Validation:** Validates incoming requests and handles invalid inputs.
- **Monitoring Dashboard:** Tracks request activity, model usage, latency, failures, and token consumption.
- **Persistent Metrics:** Stores request information in SQLite.
- **Automated Testing:** Includes tests for routing, permissions, privacy, error handling, and fallback behaviour.

## Architecture

RouteWise follows a modular architecture in which the gateway handles incoming requests, the provider layer communicates with different AI backends, and the monitoring layer records request information.

```text
                 User / Client Application
                           |
                           v
                  +------------------+
                  |   FastAPI        |
                  |   Gateway        |
                  +------------------+
                           |
                           v
                  +------------------+
                  | Request          |
                  | Validation       |
                  +------------------+
                           |
                           v
                  +------------------+
                  | Routing &        |
                  | Security Checks  |
                  +------------------+
                           |
                           v
                  +------------------+
                  | Provider Layer   |
                  +------------------+
                           |
              +------------+-------------+
              |                          |
              v                          v
       +--------------+          +---------------+
       | Local Ollama |          | LiteLLM       |
       | Adapter      |          | Adapter       |
       +--------------+          +---------------+
              |                          |
         +----+----+               +-----+------+
         |         |               |            |
         v         v               v            v
       Qwen     Qwen Coder      DeepSeek      Claude
       General                    API           API
         |         |               |            |
         +---------+---------------+------------+
                           |
                           v
                  +------------------+
                  | Model Response   |
                  +------------------+
                           |
                           v
                  +------------------+
                  | Metrics Recording|
                  +------------------+
                           |
                           v
                  +------------------+
                  | SQLite Database  |
                  +------------------+
                           |
                           v
                  +------------------+
                  | Streamlit        |
                  | Dashboard        |
                  +------------------+
```

Hosted inference is subject to security checks and paid API permissions. Paid API access is disabled by default.

## Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python 3.12 |
| API Framework | FastAPI |
| ASGI Server | Uvicorn |
| Local Model Runtime | Ollama |
| General Model | Qwen 2.5 1.5B |
| Coding Model | Qwen 2.5 Coder 1.5B |
| Hosted Models | DeepSeek, Anthropic Claude |
| Provider Integration | LiteLLM |
| HTTP Client | HTTPX |
| Database | SQLite |
| Dashboard | Streamlit |
| Data Processing | Pandas |
| Testing | Pytest |

## Supported Models

| Model Alias | Description |
|---|---|
| `auto` | Routes according to the requested task |
| `local` | Uses the default local general model |
| `general` | Handles general-purpose questions |
| `coding` | Handles programming-related questions |
| `remote` | Connects to a remote Ollama backend |
| `deepseek` | Sends requests to the hosted DeepSeek API |
| `claude` | Sends requests to the hosted Anthropic Claude API |

Local models run through Ollama. Hosted models require valid API credentials and the appropriate permissions.

## Request Routing and Fallback

RouteWise supports both automatic task-based routing and explicit model selection.

For automatic routing, the client provides a task value such as `general` or `coding`. The gateway uses that value to select the corresponding local model.

For explicit selection, the client can request a particular backend, such as DeepSeek or Claude.

Examples:

- General questions are routed to Qwen 2.5 1.5B.
- Coding questions are routed to Qwen 2.5 Coder 1.5B.
- Explicit DeepSeek requests are sent to the hosted DeepSeek API when permissions allow.
- Explicit Claude requests are sent to the Anthropic API when permissions allow.

When fallback is enabled, a failed hosted-model request can fall back to the local general model. Local requests do not automatically fall back to paid hosted models.

## Security and Configuration

RouteWise uses environment variables to configure hosted model access.

Create a `.env` file in the project root:

```env
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_MODEL=deepseek-flash

ANTHROPIC_API_KEY=your_anthropic_api_key
CLAUDE_MODEL=claude-sonnet-4-6

ENABLE_PAID_APIS=false

REMOTE_MODEL=qwen2.5:1.5b
REMOTE_BASE=http://127.0.0.1:11435
```

Replace the placeholders with the appropriate configuration values. Never publish your actual API keys.

### Security Rules

- Paid API access is disabled by default.
- Hosted requests require operator-level permission and request-level permission.
- Requests marked as sensitive are blocked from hosted inference.
- Missing API credentials prevent hosted inference.
- Hosted model failures can fall back to local inference when enabled.
- The `.env` file is excluded through `.gitignore`.
- `.env.example` provides configuration placeholders.
- API keys should never be exposed in logs, API responses, or public repositories.

Keep `ENABLE_PAID_APIS=false` unless hosted inference is intentionally enabled after reviewing the provider's pricing.

## Installation and Setup

### Prerequisites

- Python 3.12 or a compatible version
- Ollama
- Git
- Required Python dependencies

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

Create a `.env` file in the project root using the configuration described in the Security and Configuration section.

Hosted API keys are required only when using the corresponding hosted providers.

### 6. Start the Gateway

```bash
uvicorn gateway:app --reload
```

The API will be available at:

`http://127.0.0.1:8000`

### 7. Open API Documentation

Visit:

`http://127.0.0.1:8000/docs`

Use the interactive Swagger UI to inspect endpoints and send requests.

### 8. Start the Monitoring Dashboard

Open another terminal, activate the virtual environment, navigate to the project directory, and run:

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

Example request for a hosted DeepSeek model:

```json
{
  "model": "deepseek",
  "messages": [
    {
      "role": "user",
      "content": "Explain how an API gateway works."
    }
  ],
  "max_tokens": 100,
  "allow_fallback": true,
  "sensitive": false,
  "allow_paid": true
}
```

The hosted request is accepted only when paid API access is enabled on the server and the request-level permission is also provided.

The gateway validates the request, selects the backend, communicates with the selected model, and returns the response.

## Monitoring and Metrics

RouteWise uses SQLite to store request information and Streamlit to display monitoring data.

The monitoring dashboard tracks:

- Total requests and failed requests.
- Request status codes.
- Selected backend and requested model.
- Model attempts.
- Whether fallback was used.
- Response latency.
- Input and output token usage, when available.
- Sensitive-request status.
- Paid API permission status.
- Request location.

### Monitoring Workflow

1. Start the FastAPI gateway.
2. Open `/docs` and send requests.
3. Refresh the Streamlit dashboard.
4. Review request counts, backend information, failures, fallback details, and token usage.

The dashboard provides visibility into how requests are handled across local and hosted backends.

## Testing

Run the gateway test suite from the project root:

```bash
python -m pytest test_gateway.py -q
```

**Latest verified result: 19 tests passed.**

The automated tests cover:

- Gateway health and request validation.
- Local model routing.
- Hosted model permission checks.
- Sensitive-request restrictions.
- Remote backend routing.
- Backend error handling.
- Fallback from hosted and remote backends to local inference.

Python syntax can be checked using:

```bash
python -m py_compile gateway.py providers.py metrics_db.py
```

### Live DeepSeek Verification

A real DeepSeek request was successfully sent through the FastAPI gateway.

Verified results:

- HTTP status: `200`
- Backend: `deepseek`
- Model: `deepseek-flash`
- Input tokens: 37
- Output tokens: 10
- Request recorded in SQLite.
- Request visible in the Streamlit monitoring dashboard.

The API request completed successfully. The short test response used its available output tokens for reasoning, so visible response text was not returned in that particular test.

Automated fallback tests use mocks and do not require additional hosted API calls.

## Project Structure

```text
RouteWise/
│
├── gateway.py
├── providers.py
├── metrics_db.py
├── dashboard.py
├── test_gateway.py
├── local_demo.py
│
├── README.md
├── requirements.txt
├── .gitignore
├── .env.example
│
└── .venv/
```

The `.env` file contains local configuration and is intentionally excluded from version control.

## Current Project Status

RouteWise currently includes:

- A FastAPI-based AI gateway.
- Local general-purpose and coding models through Ollama.
- Hosted DeepSeek integration through LiteLLM.
- Claude provider configuration.
- Request-based model selection.
- Paid API permission controls.
- Sensitive-request protection.
- Fallback mechanisms.
- SQLite-based request tracking.
- A Streamlit monitoring dashboard.
- Automated gateway tests.

A real DeepSeek gateway request has been verified and recorded in the monitoring dashboard.

## Future Improvements

Potential areas for further development include:

- Intelligent classification of user prompts for automatic model selection.
- More hosted model integrations.
- Improved performance and latency comparisons.
- Expanded integration testing.
- More detailed monitoring and operational analytics.
- Remote backend deployment and reliability improvements.

## License

A license has not yet been specified. An appropriate license can be added before distributing the project under explicit open-source terms.
