from fastapi.testclient import TestClient
from gateway import app

client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["gateway"] == "running"


def test_invalid_role():
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "local",
            "messages": [
                {"role": "visitor", "content": "Hello"}
            ],
            "max_tokens": 100,
            "stream": False,
        },
    )

    assert response.status_code == 422


def test_empty_content():
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "local",
            "messages": [
                {"role": "user", "content": ""}
            ],
            "max_tokens": 100,
            "stream": False,
        },
    )

    assert response.status_code == 422
def test_valid_chat():
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "local",
            "messages": [
                {"role": "user", "content": "Say hello in one sentence."}
            ],
            "max_tokens": 50,
            "stream": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["choices"][0]["message"]["content"]
def test_ollama_unavailable():
    from unittest.mock import patch
    import httpx

    with patch(
        "gateway.httpx.AsyncClient.post",
        side_effect=httpx.ConnectError("Connection failed"),
    ):
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "local",
                "messages": [
                    {"role": "user", "content": "Hello"}
                ],
                "max_tokens": 50,
                "stream": False,
            },
        )

    assert response.status_code == 503
def test_ollama_timeout():
    import httpx
    from unittest.mock import patch

    with patch(
        "gateway.httpx.AsyncClient.post",
        side_effect=httpx.TimeoutException("Request timed out"),
    ):
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "local",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 50,
                "stream": False,
            },
        )

    assert response.status_code == 504


def test_ollama_server_error():
    from unittest.mock import patch, MagicMock

    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = __import__(
        "httpx"
    ).HTTPStatusError(
        "Server error",
        request=MagicMock(),
        response=MagicMock(),
    )

    with patch(
        "gateway.httpx.AsyncClient.post",
        return_value=mock_response,
    ):
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "local",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 50,
                "stream": False,
            },
        )

    assert response.status_code == 502
def test_deepseek_blocked_when_paid_apis_disabled():
    from unittest.mock import patch

    with patch("providers.PAID_APIS_ENABLED", False):
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "deepseek",
                "messages": [{"role": "user", "content": "Hello"}],
                "allow_paid": True,
                "sensitive": False,
            },
        )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Paid API use requires server and request permission."
    )

def test_deepseek_blocked_for_sensitive_request():
    from unittest.mock import patch

    with patch("providers.PAID_APIS_ENABLED", True), patch.dict(
        "os.environ", {"DEEPSEEK_API_KEY": "test-key"}
    ):
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "deepseek",
                "messages": [
                    {"role": "user", "content": "Private information"}
                ],
                "allow_paid": True,
                "sensitive": True,
            },
        )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Sensitive requests cannot use hosted models."
    )

def test_auto_coding_uses_local_coding_model():
    from unittest.mock import patch, MagicMock

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [
            {"message": {"content": "Here is the code."}}
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 8},
    }
    mock_response.raise_for_status.return_value = None

    with patch(
        "gateway.httpx.AsyncClient.post",
        return_value=mock_response,
    ) as mock_post:
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "auto",
                "task": "coding",
                "messages": [
                    {"role": "user", "content": "Write a Python function."}
                ],
                "sensitive": True,
                "allow_paid": True,
            },
        )

    assert response.status_code == 200
    assert mock_post.call_args.kwargs["json"]["model"] == (
        "qwen2.5-coder:1.5b"
    )
    assert "api.deepseek.com" not in mock_post.call_args.args[0]
def test_deepseek_fallback_to_local_general():
    from unittest.mock import patch
    import httpx

    mock_result = {
        "choices": [
            {"message": {"content": "Local fallback response"}}
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 8},
    }

    with patch("providers.PAID_APIS_ENABLED", True), patch.dict(
        "os.environ", {"DEEPSEEK_API_KEY": "test-key"}
    ), patch(
        "gateway.complete",
        side_effect=[
            httpx.ConnectError("DeepSeek unavailable"),
            mock_result,
        ],
    ) as mock_complete:
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "deepseek",
                "messages": [
                    {"role": "user", "content": "Explain an API gateway"}
                ],
                "allow_paid": True,
                "sensitive": False,
                "allow_fallback": True,
            },
        )

    assert response.status_code == 200
    assert mock_complete.call_count == 2
    assert mock_complete.call_args_list[0].kwargs["alias"] == "deepseek"
    assert mock_complete.call_args_list[1].kwargs["alias"] == "general"
    assert response.headers["X-RouteWise-Fallback"] == "true"


def test_claude_blocked_when_paid_apis_disabled():
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "claude",
            "task": "general",
            "messages": [{"role": "user", "content": "Hello"}],
            "allow_paid": True,
            "sensitive": False,
        },
    )

    assert response.status_code == 403


def test_claude_blocked_for_sensitive_request():
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "claude",
            "task": "general",
            "messages": [{"role": "user", "content": "Hello"}],
            "allow_paid": True,
            "sensitive": True,
        },
    )

    assert response.status_code == 403
def test_claude_fallback_to_local_general():
    from unittest.mock import patch
    import httpx

    mock_result = {
        "choices": [
            {"message": {"content": "Local fallback response"}}
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 8},
    }

    with patch("providers.PAID_APIS_ENABLED", True), patch.dict(
        "os.environ", {"ANTHROPIC_API_KEY": "test-key"}
    ), patch(
        "gateway.complete",
        side_effect=[
            httpx.ConnectError("Claude unavailable"),
            mock_result,
        ],
    ) as mock_complete:
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "claude",
                "messages": [
                    {"role": "user", "content": "Explain an API gateway"}
                ],
                "allow_paid": True,
                "sensitive": False,
                "allow_fallback": True,
            },
        )

    assert response.status_code == 200
    assert mock_complete.call_count == 2
    assert mock_complete.call_args_list[0].kwargs["alias"] == "claude"
    assert mock_complete.call_args_list[1].kwargs["alias"] == "general"
    assert response.headers["X-RouteWise-Fallback"] == "true"
