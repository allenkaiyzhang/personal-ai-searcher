from __future__ import annotations

import httpx
from bs4 import BeautifulSoup

from app.config import get_settings
from app.providers.base import SearchProvider, SearchResult
from app.utils.normalize import normalize_text, normalize_url


class BingHtmlSearchProvider(SearchProvider):
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    def __init__(self, search_url: str | None = None) -> None:
        self.search_url = search_url or get_settings().bing_search_url

    async def search(self, query: str, max_results: int, market: str | None = None) -> list[SearchResult]:
        params: dict[str, str | int] = {"q": query, "count": max_results}
        if market:
            params["mkt"] = market
        async with httpx.AsyncClient(timeout=10.0, headers={"User-Agent": self.user_agent}) as client:
            response = await client.get(self.search_url, params=params)
            response.raise_for_status()
        return self.parse_results(response.text, max_results=max_results)

    @staticmethod
    def parse_results(html: str, max_results: int) -> list[SearchResult]:
        soup = BeautifulSoup(html, "html.parser")
        results: list[SearchResult] = []
        seen_urls: set[str] = set()

        for item in soup.select("li.b_algo"):
            title_node = item.select_one("h2")
            link_node = item.select_one("h2 a[href]")
            snippet_node = item.select_one(".b_caption p")
            if title_node is None or link_node is None:
                continue

            title = normalize_text(title_node.get_text(" ", strip=True))
            raw_url = link_node.get("href", "")
            if not title or not raw_url:
                continue

            url = normalize_url(raw_url)
            if url in seen_urls:
                continue

            seen_urls.add(url)
            snippet = normalize_text(snippet_node.get_text(" ", strip=True)) if snippet_node else ""
            results.append(SearchResult(title=title, url=url, snippet=snippet))
            if len(results) >= max_results:
                break

        return results
