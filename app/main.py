from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from app.db.init_db import init_db
from app.db.repository import Repository
from app.db.session import get_db
from app.pipeline.query_rewriter import QueryRewriter
from app.pipeline.research_pipeline import ResearchPipeline
from app.providers.base import SearchResult
from app.providers.bing_html import BingHtmlSearchProvider
from app.schemas import (
    ExternalSearchResponse,
    ResearchRequest,
    ResearchResponse,
    RewrittenQuery,
    SearchRequest,
    SearchResponse,
    SearchResultRead,
    TimelineEventRead,
    TopicCreate,
    TopicRead,
)
from app.security import require_api_key
from app.utils.normalize import normalize_url


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(title="personal-ai-searcher", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "personal-ai-searcher"}


@app.post("/topics", response_model=TopicRead, dependencies=[Depends(require_api_key)])
def create_topic(payload: TopicCreate, db: Session = Depends(get_db)) -> TopicRead:
    return Repository(db).create_topic(payload.name, payload.aliases, payload.description)


@app.get("/topics", response_model=list[TopicRead], dependencies=[Depends(require_api_key)])
def list_topics(db: Session = Depends(get_db)) -> list[TopicRead]:
    return Repository(db).list_topics()


@app.get("/timeline/{topic_id}", response_model=list[TimelineEventRead], dependencies=[Depends(require_api_key)])
def get_timeline(topic_id: int, db: Session = Depends(get_db)) -> list[TimelineEventRead]:
    return Repository(db).recent_timeline(topic_id, limit=100)


@app.post("/search", response_model=SearchResponse, dependencies=[Depends(require_api_key)])
async def search(payload: SearchRequest) -> SearchResponse:
    provider = BingHtmlSearchProvider()
    rewritten_queries = (
        await QueryRewriter().rewrite(payload.query, payload.market)
        if payload.rewrite_query
        else [RewrittenQuery(query=payload.query, market=payload.market, language=None, reason="original query")]
    )

    try:
        results = await _run_search_queries(provider, rewritten_queries, payload.max_results)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Search provider request failed") from exc

    return SearchResponse(
        query=payload.query,
        results=[
            SearchResultRead(
                title=result.title,
                url=result.url,
                snippet=result.snippet or None,
                rank=index,
                source="bing",
            )
            for index, result in enumerate(results, start=1)
        ],
        rewritten_queries=rewritten_queries,
    )


@app.post("/api/v1/search", response_model=ExternalSearchResponse, dependencies=[Depends(require_api_key)])
async def external_search(payload: SearchRequest) -> ExternalSearchResponse:
    return ExternalSearchResponse(data=await search(payload))


async def _run_search_queries(
    provider: BingHtmlSearchProvider,
    rewritten_queries: list[RewrittenQuery],
    max_results: int,
) -> list[SearchResult]:
    results: list[SearchResult] = []
    seen_urls: set[str] = set()

    for rewritten_query in rewritten_queries:
        query_results = await provider.search(
            rewritten_query.query,
            max_results=max_results,
            market=rewritten_query.market,
        )
        for result in query_results:
            normalized_url = normalize_url(result.url)
            if not normalized_url or normalized_url in seen_urls:
                continue
            seen_urls.add(normalized_url)
            results.append(SearchResult(title=result.title, url=normalized_url, snippet=result.snippet))
            if len(results) >= max_results:
                return results

    return results


@app.post("/research", response_model=ResearchResponse, dependencies=[Depends(require_api_key)])
async def research(payload: ResearchRequest, db: Session = Depends(get_db)) -> ResearchResponse:
    pipeline = ResearchPipeline(Repository(db), BingHtmlSearchProvider())
    return await pipeline.run(payload)
