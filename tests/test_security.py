from fastapi.testclient import TestClient

import app.config as config
from app.main import app
from app.providers.base import SearchResult
from app.providers.bing_html import BingHtmlSearchProvider


async def _fake_search(
    self: BingHtmlSearchProvider,
    query: str,
    max_results: int,
    market: str | None = None,
) -> list[SearchResult]:
    return [
        SearchResult(
            title="Search result",
            url="https://example.com/result",
            snippet="A search result.",
        )
    ]


def test_search_allows_request_when_api_key_is_empty(monkeypatch) -> None:
    monkeypatch.setattr(config, "API_KEY", "")
    monkeypatch.setattr(BingHtmlSearchProvider, "search", _fake_search)
    client = TestClient(app)

    response = client.post("/search", json={"query": "temporary search"})

    assert response.status_code == 200


def test_health_does_not_require_api_key(monkeypatch) -> None:
    monkeypatch.setattr(config, "API_KEY", "secret")
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200


def test_search_rejects_missing_api_key(monkeypatch) -> None:
    monkeypatch.setattr(config, "API_KEY", "secret")
    monkeypatch.setattr(BingHtmlSearchProvider, "search", _fake_search)
    client = TestClient(app)

    response = client.post("/search", json={"query": "temporary search"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing API key"}


def test_search_rejects_wrong_api_key(monkeypatch) -> None:
    monkeypatch.setattr(config, "API_KEY", "secret")
    monkeypatch.setattr(BingHtmlSearchProvider, "search", _fake_search)
    client = TestClient(app)

    response = client.post(
        "/search",
        headers={"X-API-Key": "wrong"},
        json={"query": "temporary search"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing API key"}


def test_search_accepts_correct_api_key(monkeypatch) -> None:
    monkeypatch.setattr(config, "API_KEY", "secret")
    monkeypatch.setattr(BingHtmlSearchProvider, "search", _fake_search)
    client = TestClient(app)

    response = client.post(
        "/search",
        headers={"X-API-Key": "secret"},
        json={"query": "temporary search"},
    )

    assert response.status_code == 200
