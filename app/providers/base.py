from dataclasses import dataclass


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str


class SearchProvider:
    async def search(self, query: str, max_results: int, market: str | None = None) -> list[SearchResult]:
        raise NotImplementedError
