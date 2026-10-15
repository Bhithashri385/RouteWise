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
