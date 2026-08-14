from fastapi.testclient import TestClient

from api import app


client = TestClient(app)


def test_chat_returns_specific_error_detail(monkeypatch):
    import api

    async def fake_run_iterative_gmail_agent(**kwargs):
        raise RuntimeError("Gmail API quota exceeded")

    monkeypatch.setattr(api, "run_iterative_gmail_agent", fake_run_iterative_gmail_agent)
    monkeypatch.setattr(api, "is_gmail_connected", lambda: True)
    monkeypatch.setattr(api, "has_groq_configuration", lambda: True)

    response = client.post(
        "/api/chat",
        json={
            "message": "Check my inbox",
            "conversation_history": [],
        },
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Gmail API quota exceeded"
