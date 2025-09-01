# Repository Guidelines

## Project Structure & Module Organization
- `src/`: Flask app modules — `app.py` (factory), `routes.py` (endpoints), `services.py` (business logic), `models.py` (dataclasses).
- `templates/` and `static/`: Jinja templates and static assets.
- `data/`: JSON inputs (`stores.json`, `benefits.json`, `themes.json`).
- `storage/`: Generated artifacts (e.g., saved passes, redemptions.json).
- `config/`: Deployment/runtime config (e.g., `gunicorn.conf.py`).
- `docs/`: Additional guides. Entry point is `main.py`.

## Build, Test, and Development Commands
- Create venv: `python -m venv .venv && source .venv/bin/activate`
- Install deps: `pip install -r requirements.txt`
- Run locally: `python main.py` (serves on `http://localhost:8080`).
- Prod-like run: `gunicorn -c config/gunicorn.conf.py main:app`
- Env vars: set in `.env` (e.g., `GEMINI_API_KEY`, optional `KAKAO_API_KEY`).

## Coding Style & Naming Conventions
- Style: PEP 8, 4-space indentation, max line length ~88–100.
- Naming: modules and functions `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE_CASE`.
- Imports: stdlib → third-party → local; avoid wildcard imports.
- Structure: keep route handlers in `routes.py`, non-HTTP logic in `services.py`, shared types in `models.py`. Use the app factory `create_app()`.

## Testing Guidelines
- Framework: pytest is recommended (not yet included). Add tests under `tests/` as `test_*.py`.
- Example: use Flask test client via the factory.
  - `app = create_app(); client = app.test_client()`
- Run tests: `pytest -q` (after installing `pytest`). Target critical logic in `services.py` and route behaviors.

## Commit & Pull Request Guidelines
- Commits: concise, imperative, scoped. Examples: `fix: 로그인 세션 초기화`, `feat(routes): add /health`.
- PRs: include purpose, summary of changes, test steps, and screenshots for UI changes. Link issues (e.g., `Closes #123`). Keep PRs focused and small.
- Before opening: run app locally, verify main flows (auth, pass generation, detail view), and ensure no secrets in diffs.

## Security & Configuration Tips
- Do not commit `.env` or generated files in `storage/`.
- Required env: `GEMINI_API_KEY`. Optional: `KAKAO_API_KEY`, `PORT`.
- Session storage writes to `flask_session/` in dev; ensure the directory exists or is writable.
