from functools import lru_cache
import os

from pydantic import BaseModel


API_KEY = os.getenv("API_KEY", "")


class Settings(BaseModel):
    database_url: str = "sqlite:///./data/searcher.db"
    bing_search_url: str = "https://www.bing.com/search"
    api_key: str = ""
    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"
    enable_query_rewrite: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings(
        database_url=os.getenv("DATABASE_URL", "sqlite:///./data/searcher.db"),
        bing_search_url=os.getenv("BING_SEARCH_URL", "https://www.bing.com/search"),
        api_key=os.getenv("API_KEY", ""),
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY"),
        deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"),
        enable_query_rewrite=os.getenv("ENABLE_QUERY_REWRITE", "0") == "1",
    )
