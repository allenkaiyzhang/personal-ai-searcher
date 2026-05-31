# personal-ai-searcher

`personal-ai-searcher` is a FastAPI-based personal research search service. It provides raw search, topic memory, timeline, and research endpoints, with SQLite as the MVP persistence layer.

The production entrypoint is:

```bash
app.main:app
```

The service is designed to run on a VPS with `venv + systemd`. The default VPS path is `/opt/personal-ai-searcher`, the runtime user is `deploy`, and the API listens on `127.0.0.1:8020`.

## Features

- `GET /health`: local health check that does not call external APIs.
- `POST /search`: raw search endpoint.
- `POST /research`: research-memory pipeline.
- `POST /topics`, `GET /topics`, `GET /timeline/{topic_id}`: topic and timeline APIs.
- Optional API key protection with `API_KEY`.
- Optional query rewrite with DeepSeek.

## Directory Structure

```text
app/                         FastAPI app and business logic
config/registry.yml          non-sensitive configuration registry
tests/                       pytest test suite
scripts/deploy.sh            VPS deployment script
scripts/smoke_test.sh        VPS health smoke test
scripts/tail_logs.sh         systemd journal helper
systemd/personal-ai-searcher.service
.github/workflows/ci.yml     GitHub Actions CI
.github/workflows/deploy.yml GitHub Actions manual VPS deployment
.env.example                 environment template
requirements.txt             Python dependencies
```

## Configuration Registry

Non-sensitive configuration lives in `config/registry.yml`. Treat this file as the registry for repeated deployment, runtime, and provider defaults.

Examples stored in the registry:

```yaml
service:
  name: personal-ai-searcher

server:
  project_root: /opt/personal-ai-searcher

network:
  host: 127.0.0.1
  port: 8020
  health_url: http://127.0.0.1:8020/health

database:
  url: sqlite:///./data/searcher.db

query_rewrite:
  enabled: false
  deepseek_base_url: https://api.deepseek.com
  deepseek_model: deepseek-v4-flash
```

Add future non-sensitive settings to `config/registry.yml` first. Do not duplicate them into `.env`.

## Secrets

`.env` is reserved for sensitive values only. Create a local or server `.env` from the template:

```bash
cp .env.example .env
```

Minimum server example:

```bash
API_KEY=replace-with-strong-token
API_TOKEN=replace-with-strong-token
GOOGLE_CSE_API_KEY=replace-me-if-needed
DEEPSEEK_API_KEY=replace-me-if-needed
```

Do not commit real secrets.

## Local Development

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.db.init_db
uvicorn app.main:app --host 127.0.0.1 --port 8020 --reload
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.db.init_db
uvicorn app.main:app --host 127.0.0.1 --port 8020 --reload
```

Health check:

```bash
curl -fsS http://127.0.0.1:8020/health
```

Expected response:

```json
{"status":"ok","service":"personal-ai-searcher"}
```

## Tests

Run the test suite:

```bash
pytest -q
```

Run the same basic compile check used by CI:

```bash
python -m compileall .
```

CI does not require real external search or LLM calls.

## VPS Deployment

Expected server layout:

```bash
/opt/personal-ai-searcher
```

The repository should already be cloned there and owned or writable by the `deploy` user used by GitHub Actions SSH.

Create the server `.env`:

```bash
cd /opt/personal-ai-searcher
cp .env.example .env
nano .env
```

Run manual deployment on the VPS:

```bash
chmod +x scripts/deploy.sh scripts/smoke_test.sh scripts/tail_logs.sh
scripts/deploy.sh
scripts/smoke_test.sh
```

`scripts/deploy.sh` installs dependencies into `.venv`, initializes local resources, installs the systemd unit, restarts `personal-ai-searcher`, prints service status, and exits. It does not run `uvicorn` in the foreground.

## GitHub Actions

CI runs on:

- push to `main`
- pull requests to `main`
- manual `workflow_dispatch`

Manual deployment is available from the `Deploy to VPS` workflow.

Required GitHub Secrets:

```text
VPS_HOST
VPS_USER
VPS_SSH_KEY
VPS_PORT
```

The deploy workflow logs in as `VPS_USER`, changes to `/opt/personal-ai-searcher`, runs `git pull --ff-only`, then runs:

```bash
scripts/deploy.sh
scripts/smoke_test.sh
```

The workflow connects directly as the configured deploy user and does not switch users inside the SSH script.

## systemd

Service file:

```bash
systemd/personal-ai-searcher.service
```

Important defaults:

```text
WorkingDirectory=/opt/personal-ai-searcher
EnvironmentFile=/opt/personal-ai-searcher/.env
ExecStart=/opt/personal-ai-searcher/.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8020
User=deploy
Group=deploy
```

Manage the service:

```bash
sudo systemctl status personal-ai-searcher
sudo systemctl restart personal-ai-searcher
sudo systemctl stop personal-ai-searcher
```

## Logs

Use the helper:

```bash
scripts/tail_logs.sh
```

Or call `journalctl` directly:

```bash
sudo journalctl -u personal-ai-searcher -n 100 --no-pager
sudo journalctl -u personal-ai-searcher -f
```

Deployment script logs are appended to:

```bash
deploy.log
```

## Smoke Test

Run:

```bash
scripts/smoke_test.sh
```

By default it checks:

```bash
http://127.0.0.1:8020/health
```

Override when needed:

```bash
HEALTH_URL=http://127.0.0.1:8020/health scripts/smoke_test.sh
```

## Troubleshooting

`.env missing`: create `/opt/personal-ai-searcher/.env` from `.env.example`.

`sudo password required`: allow the `deploy` user to run the needed `systemctl`, `cp` to `/etc/systemd/system`, and `journalctl` commands, or run deployment from an account with appropriate sudo permissions.

`git pull permission denied`: verify `/opt/personal-ai-searcher` ownership, deploy key access, and that GitHub Actions logs in as the same `deploy` user.

`service failed`: run `sudo systemctl --no-pager --full status personal-ai-searcher` and `sudo journalctl -u personal-ai-searcher -n 100 --no-pager`.

`health check failed`: confirm the service is listening on `127.0.0.1:8020`, the systemd unit uses `app.main:app`, and `.env` does not contain invalid values.

## API Examples

Health:

```bash
curl -fsS http://127.0.0.1:8020/health
```

Raw search:

```bash
curl -X POST http://127.0.0.1:8020/search \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <API_KEY>" \
  -d '{"query":"OpenAI API web search","max_results":5,"market":"en-US","rewrite_query":false}'
```

Research:

```bash
curl -X POST http://127.0.0.1:8020/research \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <API_KEY>" \
  -d '{"query":"Is DRAM still in an upcycle?","topic_hint":"DRAM","max_results":5,"use_memory":true,"update_memory":true}'
```

## Roadmap

- PostgreSQL for multi-user production workloads.
- Stronger provider abstraction for search backends.
- LLM-based evidence extraction.
- Vector retrieval for long-term research memory.
