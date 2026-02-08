## Copilot Instructions

### Architecture and key flows
- This is a FastAPI modular monolith. [app/main.py](../app/main.py) wires routers from app/modules/*/router.py and serves static content from app/static.
- Module pattern: each module has router.py (HTTP), schemas.py (Pydantic), and service.py (business). Routers should call service functions, not embed logic.
- Database stack: SQLAlchemy 2.0 models live in [app/models.py](../app/models.py) with Base in [app/core/database.py](../app/core/database.py). Alembic uses Base.metadata in [alembic/env.py](../alembic/env.py).
- Settings: [app/core/config.py](../app/core/config.py) uses Pydantic Settings with .env; required vars include APP_NAME, ENVIRONMENT, DATABASE_URL, REDIS_URL, SECRET_KEY.
- Auth is JWT-based in app/modules/auth. Use Bearer tokens and `get_current_user` for user-scoped access.

### Domain-specific behavior
- Email parsing flow: [app/modules/email_parser/parser.py](../app/modules/email_parser/parser.py) detects bank and applies regex parsers, returning ParsedTransaction. [app/modules/email_parser/service.py](../app/modules/email_parser/service.py) builds drafts/creates, and parse-and-create ingests RawEmail then creates Transaction.
- AI categorizer is rule-based in [app/modules/ai_agent/rules.py](../app/modules/ai_agent/rules.py); normalize removes accents; service scans keywords and falls back to "Outros".
- Gmail sync uses Google APIs in [app/modules/gmail_sync/service.py](../app/modules/gmail_sync/service.py) and router in [app/modules/gmail_sync/router.py](../app/modules/gmail_sync/router.py); OAuth state/credentials are persisted in Redis with a TTL for the state. Uses env vars GMAIL_CLIENT_ID/SECRET/PROJECT_ID/REDIRECT_URI.
- Budget summary uses rolling windows and optional subcategory expansion via BFS in [app/modules/budgets/service.py](../app/modules/budgets/service.py).
- Seed data is in [app/seeds/categories.py](../app/seeds/categories.py); seeding logic is in [app/modules/categories/service.py](../app/modules/categories/service.py).

### Workflows
- Start infra: `docker-compose up` (Postgres 16 and Redis 7).
- Run API: `uvicorn app.main:app --reload` (serves / and /static).
- Run migrations: `alembic upgrade head` (uses DATABASE_URL).
- Tests: pytest-based tests live in tests/ (run `python -m pytest`).
