import secrets

import app.config as config
from fastapi import Header, HTTPException


async def require_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    if not config.API_KEY:
        return
    if x_api_key is None or not secrets.compare_digest(x_api_key, config.API_KEY):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
