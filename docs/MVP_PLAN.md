# MVP Plan — Assessor Financeiro

## 1. Project Analysis

### What exists today

| Module | Status | Test Coverage |
|---|---|---|
| **Auth** (JWT register/login/me) | ✅ Complete | Indirect (3 tests) |
| **Accounts** (full CRUD) | ✅ Complete | 2 tests |
| **Categories** (create/list/get + seed) | ⚠️ Partial — no update/delete | None |
| **Transactions** (full CRUD + filters) | ✅ Complete | None |
| **Budgets** (create/list/summary with BFS) | ⚠️ Partial — no update/delete | None |
| **Email Parser** (5 banks + generic fallback) | ✅ Complete | 5 tests |
| **AI Categorizer** (rule-based, 34 rules) | ✅ Complete (returns names, not IDs) | 2 tests |
| **Gmail Sync** (OAuth + full sync pipeline) | ✅ Complete | None |
| **Notifications** | ❌ Stub only | None |
| **Frontend** (single-page HTML) | ⚠️ Basic — accounts, transactions list, Gmail sync | N/A |

### Key Gaps

1. **No pagination** on any list endpoint — will break with real data volumes.
2. **Categories & Budgets** lack update/delete endpoints.
3. **AI Categorizer** returns category *names* but never resolves to actual `category_id` from the database.
4. **Notifications module** is a placeholder with no delivery logic.
5. **Test coverage** is very low — only email parser and auth flows are tested.
6. **Frontend** is a single HTML file with inline JS/CSS — no component structure, no dashboard, no charts.
7. **No CI/CD pipeline** — no GitHub Actions for linting, testing, or deployment.
8. **No API documentation** beyond the README — FastAPI auto-generates `/docs` but there are no schema descriptions.
9. **No data export** — users cannot export their financial data.
10. **No recurring transactions or scheduled imports**.

---

## 2. MVP Definition

### MVP Goal
> A single user can register, connect bank email notifications, automatically import and categorize transactions, set budgets, and see a summary dashboard — all through a functional web UI.

### MVP Scope (In)
- User registration and authentication
- Account CRUD
- Category CRUD (with default seed data)
- Transaction CRUD with filtering + pagination
- Email parsing (existing 5 banks)
- Gmail OAuth sync pipeline
- AI auto-categorization integrated into the transaction creation flow
- Budget creation and summary (spent vs. limit)
- Minimal responsive dashboard (totals, recent transactions, budget progress)
- CI pipeline (lint + tests)
- API documentation improvements

### MVP Scope (Out)
- Push notifications / email alerts
- Multi-currency support
- Recurring/scheduled transactions
- Data export (CSV/PDF)
- Mobile app
- Advanced AI (ML-based categorization)
- Multi-tenancy / team features

---

## 3. Implementation Milestones & GitHub Issues

### Milestone 1: Foundation & CI (Priority: Critical)

> **Goal**: Establish development workflow and quality baseline.

#### Issue #1 — Set up GitHub Actions CI pipeline
**Labels**: `infra`, `ci`, `priority:high`

**Description**:
Create `.github/workflows/ci.yml` that runs on every push and PR:

- **Lint**: `ruff check .` (add `ruff` to dev dependencies)
- **Test**: `python -m pytest --tb=short` with in-memory SQLite (already in conftest)
- **Python version**: 3.11

**Acceptance Criteria**:
- [ ] `.github/workflows/ci.yml` exists and runs on push/PR to `main`
- [ ] Ruff linter configured (pyproject.toml or ruff.toml)
- [ ] All existing tests pass in CI
- [ ] Badge added to README

---

#### Issue #2 — Add pagination to all list endpoints
**Labels**: `backend`, `enhancement`, `priority:high`

**Description**:
All `GET` list endpoints currently return unbounded results. Add `skip` and `limit` query parameters (default `skip=0`, `limit=50`, max `limit=200`).

**Affected endpoints**:
- `GET /accounts/`
- `GET /categories/`
- `GET /transactions/`
- `GET /budgets/`

**Acceptance Criteria**:
- [ ] Shared `PaginationParams` dependency in `app/core/pagination.py`
- [ ] All list service functions accept `skip` and `limit`
- [ ] Response wraps items in `{"items": [...], "total": N, "skip": 0, "limit": 50}`
- [ ] Tests for boundary cases (empty, partial page, full page)

---

#### Issue #3 — Add `.env.example` and document local setup
**Labels**: `docs`, `priority:medium`

**Description**:
Create a `.env.example` with all required variables (with placeholder values) and update the README with step-by-step local setup instructions.

**Acceptance Criteria**:
- [ ] `.env.example` file with all vars from `Settings`
- [ ] README "Quick Start" section with numbered steps
- [ ] `Makefile` or shell script with common commands (`make setup`, `make test`, `make run`)

---

### Milestone 2: Complete CRUD & Data Integrity (Priority: High)

> **Goal**: All core entities have full CRUD and proper validation.

#### Issue #4 — Add update/delete endpoints for Categories
**Labels**: `backend`, `enhancement`, `priority:high`

**Description**:
Categories currently only have create/list/get. Add:
- `PUT /categories/{id}` — update name, icon, color, parent_id
- `DELETE /categories/{id}` — only if no transactions or budgets reference it (or reassign to "Outros")

**Acceptance Criteria**:
- [ ] `CategoryUpdate` schema in `schemas.py`
- [ ] `update_category` and `delete_category` in `service.py`
- [ ] Router endpoints with proper 404/409 handling
- [ ] Prevent deleting categories with active transactions (return 409)
- [ ] Tests for update, delete, and delete-with-references

---

#### Issue #5 — Add update/delete endpoints for Budgets
**Labels**: `backend`, `enhancement`, `priority:high`

**Description**:
Budgets currently only have create/list/summary. Add:
- `PUT /budgets/{id}` — update amount_limit, period, start_date
- `DELETE /budgets/{id}`

**Acceptance Criteria**:
- [ ] `BudgetUpdate` schema
- [ ] `update_budget` and `delete_budget` in `service.py`
- [ ] Router endpoints
- [ ] Tests

---

#### Issue #6 — Add seed endpoint and auto-seed on first login
**Labels**: `backend`, `enhancement`, `priority:medium`

**Description**:
Default categories should be seeded automatically for new users. Currently `seed_default_categories` exists but is never called automatically.

**Acceptance Criteria**:
- [ ] On `POST /auth/register`, after creating user, call `seed_default_categories(db, user.id)`
- [ ] `POST /categories/seed` endpoint (idempotent) for manual re-seeding
- [ ] Test that a new user gets default categories

---

### Milestone 3: Smart Categorization Integration (Priority: High)

> **Goal**: Auto-categorization is wired into the transaction pipeline end-to-end.

#### Issue #7 — Integrate AI categorizer with database categories
**Labels**: `backend`, `enhancement`, `priority:high`

**Description**:
The AI categorizer currently returns category/subcategory **names** but never resolves to an actual `category_id`. It needs to look up the user's categories in the DB and return the matching ID.

**Implementation**:
1. Add `categorize_with_db(db, user_id, merchant, description)` to `ai_agent/service.py`
2. Query user's categories, match by normalized name
3. Return `category_id` along with names
4. Fall back to "Outros" category (create if missing)

**Acceptance Criteria**:
- [ ] New service function resolves category names → IDs from the DB
- [ ] Falls back gracefully when no match
- [ ] Unit tests with seeded categories

---

#### Issue #8 — Auto-categorize transactions on creation
**Labels**: `backend`, `enhancement`, `priority:medium`

**Description**:
When a transaction is created (manually or via email sync) **without** a `category_id`, automatically run the AI categorizer and assign the best match.

**Affected flows**:
- `POST /transactions/` (when `category_id` is null)
- `POST /email/parse-and-create`
- `POST /gmail/sync`

**Acceptance Criteria**:
- [ ] Transaction creation auto-categorizes when `category_id` is null
- [ ] Gmail sync pipeline uses auto-categorization
- [ ] User can override by providing explicit `category_id`
- [ ] Tests

---

### Milestone 4: Test Coverage (Priority: High)

> **Goal**: Reach ≥80% test coverage on business logic.

#### Issue #9 — Add transaction CRUD tests
**Labels**: `testing`, `priority:high`

**Description**:
No tests exist for the transactions module. Add comprehensive tests.

**Test cases**:
- [ ] Create transaction (valid)
- [ ] Create transaction for another user's account (403)
- [ ] List transactions with filters (date range, category, account)
- [ ] Update transaction
- [ ] Delete transaction
- [ ] Get transaction by ID (own vs. 404)

---

#### Issue #10 — Add category and budget tests
**Labels**: `testing`, `priority:high`

**Description**:
- [ ] Category CRUD tests (create, list, get, update, delete)
- [ ] Category seed test (new user gets defaults)
- [ ] Budget CRUD tests
- [ ] Budget summary calculation test (verify spent/remaining math)
- [ ] Budget with subcategory expansion (BFS) test

---

#### Issue #11 — Add email parser edge-case tests
**Labels**: `testing`, `priority:medium`

**Description**:
Expand coverage for the email parser:
- [ ] Bradesco purchase
- [ ] Inter purchase
- [ ] Generic fallback parser
- [ ] `parse_date` with 5-char format (`dd/mm`)
- [ ] Malformed/unrecognized email body
- [ ] Router endpoints (`/email/parse`, `/email/parse-to-transaction`)

---

#### Issue #12 — Add Gmail sync tests with mocked Google APIs
**Labels**: `testing`, `priority:medium`

**Description**:
Gmail sync is untested. Add tests using `unittest.mock` to mock Google API and Redis.

**Test cases**:
- [ ] `sync_gmail_emails` with mocked Gmail API returning 2 messages
- [ ] OAuth state save/retrieve from Redis (mock `redis.Redis`)
- [ ] Skip non-bank emails
- [ ] Deduplication of already-ingested messages

---

### Milestone 5: Frontend Dashboard (Priority: Medium)

> **Goal**: Replace the basic HTML with a usable dashboard.

#### Issue #13 — Restructure frontend with component-based architecture
**Labels**: `frontend`, `enhancement`, `priority:medium`

**Description**:
The current frontend is a single 1229-line HTML file with inline styles and scripts. Restructure into a maintainable SPA. Use vanilla JS modules or a lightweight framework (Alpine.js or htmx) — no heavy build step required.

**New file structure**:
```
app/static/
  index.html          (shell + nav)
  css/
    styles.css
  js/
    api.js            (API client with auth headers)
    app.js            (router/tab logic)
    accounts.js
    transactions.js
    dashboard.js
    budgets.js
    sync.js
```

**Acceptance Criteria**:
- [ ] Styles extracted to CSS file
- [ ] JS split into modules
- [ ] All existing functionality preserved
- [ ] Mobile-responsive layout

---

#### Issue #14 — Build dashboard summary view
**Labels**: `frontend`, `enhancement`, `priority:medium`

**Description**:
Add a "Dashboard" tab as the default view showing:
- **Total balance** across all accounts
- **Monthly spending** (current month total)
- **Top 5 recent transactions**
- **Budget progress bars** (spent/limit per category)

**Backend support needed**:
- `GET /accounts/summary` — returns total balance across all user accounts
- `GET /transactions/summary?period=month` — returns total spent in period

**Acceptance Criteria**:
- [ ] New backend summary endpoints
- [ ] Dashboard tab with 4 cards
- [ ] Budget progress bars (green/yellow/red based on % spent)
- [ ] Auto-refresh on tab switch

---

#### Issue #15 — Add category management UI
**Labels**: `frontend`, `enhancement`, `priority:low`

**Description**:
Add a "Categories" section in the UI where users can:
- View their category tree (parent → subcategories)
- Edit category name/icon/color
- Delete categories (with warning if referenced)

---

### Milestone 6: Production Hardening (Priority: Medium)

> **Goal**: Make the app reliable and deployable.

#### Issue #16 — Add structured logging
**Labels**: `backend`, `infra`, `priority:medium`

**Description**:
Replace `print()` calls with Python `logging` module. Use structured JSON logging for production.

**Acceptance Criteria**:
- [ ] Configure `logging` in `app/core/logging.py`
- [ ] All modules use `logger = logging.getLogger(__name__)`
- [ ] Request ID middleware for traceability
- [ ] JSON format in production, human-readable in development

---

#### Issue #17 — Add error handling middleware
**Labels**: `backend`, `enhancement`, `priority:medium`

**Description**:
Add global exception handlers for:
- `SQLAlchemyError` → 500 with safe message
- `ValidationError` → 422 (already handled by FastAPI)
- `HTTPException` → pass through
- Unhandled exceptions → 500 with request ID for debugging

**Acceptance Criteria**:
- [ ] Custom exception handlers registered in `main.py`
- [ ] Consistent error response format: `{"detail": "...", "request_id": "..."}`
- [ ] No stack traces leaked to client in production

---

#### Issue #18 — Add rate limiting
**Labels**: `backend`, `security`, `priority:low`

**Description**:
Add rate limiting to public endpoints to prevent abuse:
- `/auth/register` — 5 req/min per IP
- `/auth/token` — 10 req/min per IP
- `/email/parse` — 30 req/min per IP

Use `slowapi` or Redis-based rate limiter.

---

### Milestone 7: Documentation & Onboarding (Priority: Medium)

#### Issue #19 — Improve API documentation with OpenAPI descriptions
**Labels**: `docs`, `priority:medium`

**Description**:
FastAPI generates `/docs` automatically, but endpoints lack descriptions, examples, and response models.

**Acceptance Criteria**:
- [ ] All router endpoints have `summary` and `description` parameters
- [ ] Request/response schemas have `Field(description=..., examples=[...])` 
- [ ] Tags group endpoints logically in Swagger UI
- [ ] `/docs` page is fully self-documenting

---

#### Issue #20 — Create CONTRIBUTING.md
**Labels**: `docs`, `priority:medium`

**Description**:
Document the development workflow for contributors:
- Branch naming convention (`feature/`, `fix/`, `chore/`)
- PR template
- How to run tests locally
- Code style guide (ruff config)
- Module structure convention (router → service → schemas)
- How to add a new module

---

## 4. Recommended Implementation Order

```
Phase 1 (Week 1-2): Foundation
├── Issue #1  — CI Pipeline
├── Issue #3  — .env.example + setup docs
├── Issue #2  — Pagination
└── Issue #6  — Auto-seed categories

Phase 2 (Week 2-3): Complete Backend
├── Issue #4  — Category CRUD
├── Issue #5  — Budget CRUD
├── Issue #7  — AI ↔ DB integration
└── Issue #8  — Auto-categorize on creation

Phase 3 (Week 3-4): Test Coverage
├── Issue #9  — Transaction tests
├── Issue #10 — Category + Budget tests
├── Issue #11 — Email parser tests
└── Issue #12 — Gmail sync tests

Phase 4 (Week 4-6): Frontend & UX
├── Issue #13 — Restructure frontend
├── Issue #14 — Dashboard view
└── Issue #15 — Category management UI

Phase 5 (Week 6-7): Hardening
├── Issue #16 — Structured logging
├── Issue #17 — Error handling
└── Issue #18 — Rate limiting

Phase 6 (Week 7-8): Documentation
├── Issue #19 — OpenAPI docs
└── Issue #20 — CONTRIBUTING.md
```

## 5. Labels to Create in GitHub

| Label | Color | Description |
|---|---|---|
| `backend` | `#0075ca` | Backend/API changes |
| `frontend` | `#7057ff` | Frontend/UI changes |
| `testing` | `#bfd4f2` | Test coverage improvements |
| `infra` | `#d4c5f9` | Infrastructure and CI/CD |
| `docs` | `#0e8a16` | Documentation |
| `security` | `#e11d48` | Security improvements |
| `enhancement` | `#a2eeef` | New feature or improvement |
| `ci` | `#f9d0c4` | CI/CD pipeline |
| `priority:high` | `#b60205` | Must have for MVP |
| `priority:medium` | `#fbca04` | Should have for MVP |
| `priority:low` | `#c2e0c6` | Nice to have |

## 6. Branch Strategy

```
main (protected — requires PR + CI pass)
├── feature/1-ci-pipeline
├── feature/2-pagination
├── feature/3-env-setup-docs
├── feature/4-category-crud
├── ...
```

Each issue gets a branch named `feature/<issue-number>-<short-description>`. PRs require at least 1 review and passing CI before merge.
