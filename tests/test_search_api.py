import httpx
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.db.init_db import init_db
from app.db.models import Evidence, ResearchRun, TimelineEvent
from app.db.session import SessionLocal
from app.main import app
from app.providers.base import SearchResult
from app.providers.bing_html import BingHtmlSearchProvider


def _table_counts() -> dict[str, int]:
    with SessionLocal() as db:
        return {
            "research_runs": db.scalar(select(func.count()).select_from(ResearchRun)) or 0,
            "evidence": db.scalar(select(func.count()).select_from(Evidence)) or 0,
            "timeline_events": db.scalar(select(func.count()).select_from(TimelineEvent)) or 0,
        }


def test_search_returns_structured_results(monkeypatch) -> None:
    async def fake_search(
        self: BingHtmlSearchProvider,
        query: str,
        max_results: int,
        market: str | None = None,
    ) -> list[SearchResult]:
        assert query == "OpenAI API web search"
        assert max_results == 5
        assert market == "en-US"
        return [
            SearchResult(
                title="OpenAI API search docs",
                url="https://example.com/openai-search",
                snippet="Search API documentation.",
            )
        ]

    monkeypatch.setattr(BingHtmlSearchProvider, "search", fake_search)
    client = TestClient(app)

    response = client.post(
        "/search",
        json={"query": "OpenAI API web search", "max_results": 5, "market": "en-US"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "query": "OpenAI API web search",
        "results": [
            {
                "title": "OpenAI API search docs",
                "url": "https://example.com/openai-search",
                "snippet": "Search API documentation.",
                "rank": 1,
                "source": "bing",
            }
        ],
    }


def test_search_returns_empty_results(monkeypatch) -> None:
    async def fake_search(
        self: BingHtmlSearchProvider,
        query: str,
        max_results: int,
        market: str | None = None,
    ) -> list[SearchResult]:
        return []

    monkeypatch.setattr(BingHtmlSearchProvider, "search", fake_search)
    client = TestClient(app)

    response = client.post("/search", json={"query": "temporary search"})

    assert response.status_code == 200
    assert response.json() == {"query": "temporary search", "results": []}


def test_search_rejects_blank_query() -> None:
    client = TestClient(app)

    response = client.post("/search", json={"query": "   "})

    assert response.status_code == 422


def test_search_provider_failure_returns_502(monkeypatch) -> None:
    async def fake_search(
        self: BingHtmlSearchProvider,
        query: str,
        max_results: int,
        market: str | None = None,
    ) -> list[SearchResult]:
        request = httpx.Request("GET", "https://www.bing.com/search")
        raise httpx.ConnectError("connection failed", request=request)

    monkeypatch.setattr(BingHtmlSearchProvider, "search", fake_search)
    client = TestClient(app)

    response = client.post("/search", json={"query": "temporary search"})

    assert response.status_code == 502


def test_search_does_not_write_research_memory_tables(monkeypatch) -> None:
    async def fake_search(
        self: BingHtmlSearchProvider,
        query: str,
        max_results: int,
        market: str | None = None,
    ) -> list[SearchResult]:
        return [
            SearchResult(
                title="Standalone search result",
                url="https://example.com/standalone",
                snippet="This should not become evidence.",
            )
        ]

    init_db()
    before = _table_counts()
    monkeypatch.setattr(BingHtmlSearchProvider, "search", fake_search)
    client = TestClient(app)

    response = client.post("/search", json={"query": "standalone search"})

    assert response.status_code == 200
    assert _table_counts() == before
