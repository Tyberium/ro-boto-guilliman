from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from roboto_guilliman.api.main import app


def test_ask_rejects_legacy_edition_without_retrieval():
    state = MagicMock()
    app.state.ro_boto = state

    client = TestClient(app)
    response = client.post(
        "/v1/ask",
        json={"query": "Explain blast templates in 8th edition", "use_cache": False},
    )

    assert response.status_code == 200
    body = response.json()
    assert "heresy" in body["answer"].lower()
    assert body["context_chunks"] == []
    state.retriever.retrieve.assert_not_called()
    state.arbiter.answer.assert_not_called()
