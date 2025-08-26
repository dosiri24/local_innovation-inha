# Repository Guidelines

## Project Structure & Module Organization
- `main.py`: WSGI entrypoint (creates app via `src/app.py`).
- `src/`: core code — `app.py` (Flask factory), `routes.py` (HTTP routes), `services.py` (AI, storage), `models.py` (dataclasses).
- `templates/` + `static/`: Jinja2 views and assets.
- `data/`: JSON data (`stores.json`, `benefits.json`, `themes.json`).
- `storage/`: runtime output (`saved_passes/`).
- `config/`: deployment config (e.g., `gunicorn.conf.py`).
- `docs/`: setup and deployment notes.

## Build, Test, and Development Commands
- Setup: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
- Env: create `.env` with `GEMINI_API_KEY` (and optional `GEMINI_MODEL`).
- Run (dev): `python main.py` (serves on `http://localhost:8080`).
- Health check: `curl localhost:8080/health`
- Run (prod-like): `gunicorn -c config/gunicorn.conf.py main:app`

## Coding Style & Naming Conventions
- Python 3.10+ (repo tested on 3.13). Use PEP 8, 4‑space indents.
- Filenames and functions: `snake_case`; classes and Enums: `PascalCase`.
- Prefer type hints and `@dataclass` (see `models.py`).
- Keep side effects out of import time; use the app factory `create_app()`.
- No formatter is enforced; if used locally, run Black/ruff only on changed files.

## Testing Guidelines
- No formal test suite yet. Validate locally by:
  - Hitting `/health` and key routes (e.g., `/api/generate-pass`).
  - Verifying files in `storage/saved_passes/`.
- If adding tests, place under `tests/` (pytest) and name like `test_routes.py`.

## Commit & Pull Request Guidelines
- Messages: concise, imperative; Korean or English OK. Emoji prefixes optional (seen in history).
  - Examples: `fix: 로그인 리다이렉트 오류 수정`, `feat: add benefit-code redemption`.
- PRs: include purpose, linked issues, UI screenshots (if applicable), and repro steps.
- Ensure `.env` is not committed; update docs when changing behavior or endpoints.

## Security & Configuration Tips
- Secrets: keep `GEMINI_API_KEY` in `.env`. Do not log secrets.
- Sessions: dev uses filesystem under `flask_session/`; ensure write access.
- Cloud deploys bind to port `8080` via Gunicorn; verify health endpoint for probes.
