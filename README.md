# personal-AI-searcher

`personal-AI-searcher` is an MVP research-memory search service. It is not a generic `Query -> Result` search API. Its goal is to validate a loop:

`Topic -> Evidence -> Timeline -> Insight -> Updated Research Answer`

The service searches the web, stores evidence, maintains topic timelines, keeps historical judgments, and reuses prior research context in later searches.

## Workflow

1. Match a query to a long-running `Topic`.
2. Load previous `Insight`, `Evidence`, and `TimelineEvent` records when memory is enabled.
3. Plan one to three search queries.
4. Search Bing HTML results.
5. Fetch and extract page content.
6. Convert results into rule-based `Evidence`.
7. Create timeline updates for new evidence.
8. Update insight when enough new evidence arrives.
9. Generate a Markdown research report.

The MVP intentionally does not use an LLM. Reports are rule-based summaries and should not be considered factual conclusions.

## Search vs Research

`POST /search` is the raw search endpoint. It calls the Bing HTML search provider and returns structured search results. It does not fetch page bodies, extract evidence, update timelines, create insights, or write to the database. Use `/search` for temporary searches and for testing raw search behavior.

`POST /research` is the research-memory pipeline. It matches a topic, reuses prior memory, searches, fetches pages, extracts evidence, updates timeline events, may update insights, and records the research run. Use `/research` when results should become durable evidence and timeline history.

## DeepSeek Query Rewrite

Query rewrite is optional and disabled by default. When enabled, DeepSeek is used only to rewrite a poor user query into one to three search-engine-friendly queries. It does not answer the question, does not generate factual conclusions, and its `reason` field should be treated only as debug metadata. Final search results still come from real Bing search results.

Environment variables:

```bash
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
ENABLE_QUERY_REWRITE=0
```

Project root `.env` example:

```bash
DATABASE_URL=sqlite:///./data/searcher.db
BING_SEARCH_URL=https://www.bing.com/search
DEEPSEEK_API_KEY=your-api-key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
ENABLE_QUERY_REWRITE=1
```

For `systemd` deployments, the service reads the project root `.env` file automatically, for example `/opt/personal-AI-searcher/.env`. After changing `.env`, reload systemd and restart the service:

```bash
sudo systemctl daemon-reload
sudo systemctl restart personal-ai-searcher
```

Example `/search` request with query rewrite:

```bash
curl -sS -X POST http://127.0.0.1:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query":"How to speak VAT in CHinese",
    "max_results":5,
    "market":"en-US",
    "rewrite_query":true
  }' | python3 -m json.tool
```

## Install

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Initialize Database

```bash
python -m app.db.init_db
```

The default database URL is `sqlite:///./data/searcher.db`.

## Start Service

```bash
uvicorn app.main:app --reload
```

## One-Command Deployment

Windows PowerShell:

```powershell
.\scripts\deploy.ps1
```

Useful options:

```powershell
.\scripts\deploy.ps1 -Port 8080
.\scripts\deploy.ps1 -SkipTests
.\scripts\deploy.ps1 -NoStart
.\scripts\deploy.ps1 -RecreateVenv
.\scripts\deploy.ps1 -UpgradePip
```

Linux/macOS:

```bash
sh scripts/deploy.sh
```

Useful environment variables:

```bash
PORT=8080 sh scripts/deploy.sh
SKIP_TESTS=1 sh scripts/deploy.sh
NO_RESTART=1 sh scripts/deploy.sh
RECREATE_VENV=1 sh scripts/deploy.sh
UPGRADE_PIP=1 sh scripts/deploy.sh
RUN_GIT_PULL=1 sh scripts/deploy.sh
```

On Linux servers, `scripts/deploy.sh` assumes the long-running app process is managed by `systemd`. It prepares the virtual environment, installs dependencies, optionally runs tests, initializes SQLite, restarts the configured service, runs a health check, and exits.

## ECS systemd deployment

Clone the project on the ECS instance:

```bash
cd /opt
git clone <repo-url> personal-AI-searcher
cd /opt/personal-AI-searcher
```

Install the `systemd` service:

```bash
chmod +x scripts/install_systemd_service.sh scripts/deploy.sh
./scripts/install_systemd_service.sh
```

Run deployment:

```bash
./scripts/deploy.sh
```

Skip tests if needed:

```bash
SKIP_TESTS=1 ./scripts/deploy.sh
```

Pull the latest code and deploy:

```bash
RUN_GIT_PULL=1 ./scripts/deploy.sh
```

Check service status:

```bash
systemctl status personal-ai-searcher
```

View service logs:

```bash
journalctl -u personal-ai-searcher -f
```

Run a health check:

```bash
curl http://127.0.0.1:8000/health
```

Verify query rewrite after configuring `.env` and restarting the service:

```bash
curl -sS -X POST http://127.0.0.1:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query":"How to speak VAT in CHinese",
    "max_results":5,
    "market":"en-US",
    "rewrite_query":true
  }' | python3 -m json.tool
```

Notes:

- `deploy.sh` no longer stays attached to the foreground `uvicorn` process.
- `uvicorn` is managed by `systemd`.
- The default SQLite database is `data/searcher.db`.
- The default service listens only on `127.0.0.1`.
- For public access, put a reverse proxy such as Nginx in front of the service later. Directly exposing `0.0.0.0` is not recommended.

## API Examples

```bash
curl http://127.0.0.1:8000/health
```

Raw search:

```bash
curl -X POST http://127.0.0.1:8000/search \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"OpenAI API web search\",\"max_results\":5,\"market\":\"en-US\",\"rewrite_query\":false}"
```

```bash
curl -X POST http://127.0.0.1:8000/topics \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"DRAM Market\",\"aliases\":[\"DRAM\",\"HBM\",\"Micron\"],\"description\":\"Memory market research\"}"
```

```bash
curl -X POST http://127.0.0.1:8000/research \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"Is DRAM still in an upcycle?\",\"topic_hint\":\"DRAM\",\"max_results\":5,\"use_memory\":true,\"update_memory\":true}"
```

## Roadmap

- V2: PostgreSQL
- V3: LLM Evidence Extraction
- V4: Vector Search
- V5: Personalized Ranking
