from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from app.db.init_db import init_db
from app.db.repository import Repository
from app.db.session import get_db
from app.pipeline.research_pipeline import ResearchPipeline
from app.providers.bing_html import BingHtmlSearchProvider
from app.schemas import (
    ResearchRequest,
    ResearchResponse,
    SearchRequest,
    SearchResponse,
    SearchResultRead,
    TimelineEventRead,
    TopicCreate,
    TopicRead,
)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(title="personal-AI-searcher", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/topics", response_model=TopicRead)
def create_topic(payload: TopicCreate, db: Session = Depends(get_db)) -> TopicRead:
    return Repository(db).create_topic(payload.name, payload.aliases, payload.description)


@app.get("/topics", response_model=list[TopicRead])
def list_topics(db: Session = Depends(get_db)) -> list[TopicRead]:
    return Repository(db).list_topics()


@app.get("/timeline/{topic_id}", response_model=list[TimelineEventRead])
def get_timeline(topic_id: int, db: Session = Depends(get_db)) -> list[TimelineEventRead]:
    return Repository(db).recent_timeline(topic_id, limit=100)


@app.post("/search", response_model=SearchResponse)
async def search(payload: SearchRequest) -> SearchResponse:
    provider = BingHtmlSearchProvider()
    try:
        results = await provider.search(payload.query, payload.max_results, payload.market)
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
    )


@app.post("/research", response_model=ResearchResponse)
async def research(payload: ResearchRequest, db: Session = Depends(get_db)) -> ResearchResponse:
    pipeline = ResearchPipeline(Repository(db), BingHtmlSearchProvider())
    return await pipeline.run(payload)
