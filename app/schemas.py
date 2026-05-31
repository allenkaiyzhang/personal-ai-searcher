from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class TopicCreate(BaseModel):
    name: str
    aliases: list[str] = Field(default_factory=list)
    description: str | None = None


class TopicRead(BaseModel):
    id: int
    name: str
    aliases: list[str]
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EvidenceRead(BaseModel):
    id: int
    topic_id: int
    claim: str
    summary: str
    excerpt: str
    source_title: str
    source_url: str
    source_domain: str
    published_at: datetime | None
    retrieved_at: datetime
    confidence: float
    novelty: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TimelineEventRead(BaseModel):
    id: int
    topic_id: int
    event_date: datetime
    title: str
    description: str
    importance: float
    evidence_id: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class InsightRead(BaseModel):
    id: int
    topic_id: int
    current_view: str
    confidence: str
    updated_at: datetime

    model_config = {"from_attributes": True}


class ResearchRequest(BaseModel):
    query: str
    topic_hint: str | None = None
    max_results: int = Field(default=5, ge=1, le=20)
    use_memory: bool = True
    update_memory: bool = True
    rewrite_query: bool = False


class RewrittenQuery(BaseModel):
    query: str
    market: str | None = None
    language: str | None = None
    reason: str | None = None


class ResearchResponse(BaseModel):
    matched_topic: str | None
    old_view: str | None
    answer: str
    view_changed: bool
    timeline_updates: list[TimelineEventRead]
    new_evidence: list[EvidenceRead]
    confidence: str
    rewritten_queries: list[RewrittenQuery] = Field(default_factory=list)


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    max_results: int = Field(default=5, ge=1, le=20)
    market: str | None = "en-US"
    rewrite_query: bool = False

    @field_validator("query")
    @classmethod
    def query_must_not_be_blank(cls, value: str) -> str:
        query = value.strip()
        if not query:
            raise ValueError("query must not be blank")
        return query


class SearchResultRead(BaseModel):
    title: str
    url: str
    snippet: str | None
    rank: int
    source: str = "bing"


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultRead]
    rewritten_queries: list[RewrittenQuery] = Field(default_factory=list)


class ExternalSearchResponse(BaseModel):
    status: str = "ok"
    service: str = "personal-ai-searcher"
    data: SearchResponse
