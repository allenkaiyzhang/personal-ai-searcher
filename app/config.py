import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel
import yaml


API_KEY = os.getenv("API_KEY", "")
REGISTRY_PATH = Path(__file__).resolve().parents[1] / "config" / "registry.yml"


def _load_registry() -> dict[str, Any]:
    if not REGISTRY_PATH.exists():
        return {}
    with REGISTRY_PATH.open("r", encoding="utf-8") as registry_file:
        data = yaml.safe_load(registry_file) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Registry file must contain a YAML mapping: {REGISTRY_PATH}")
    return data


def _section(registry: dict[str, Any], key: str) -> dict[str, Any]:
    value = registry.get(key, {})
    return value if isinstance(value, dict) else {}


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
    registry = _load_registry()
    database = _section(registry, "database")
    search = _section(registry, "search")
    query_rewrite = _section(registry, "query_rewrite")

    return Settings(
        database_url=str(database.get("url", "sqlite:///./data/searcher.db")),
        bing_search_url=str(search.get("bing_search_url", "https://www.bing.com/search")),
        api_key=os.getenv("API_KEY", ""),
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY"),
        deepseek_base_url=str(query_rewrite.get("deepseek_base_url", "https://api.deepseek.com")),
        deepseek_model=str(query_rewrite.get("deepseek_model", "deepseek-v4-flash")),
        enable_query_rewrite=bool(query_rewrite.get("enabled", False)),
    )
