Phase 5 Plan
==============

Goals
- Add CI to run the test suite on push/PR.
- Add unit/integration tests for key backend endpoints used by the new frontend features (transactions, categories, auth).
- Add lint/format checks to the CI pipeline.
- Add an optional E2E smoke test suite (Playwright) to exercise the running app.
- Update documentation and open a PR for Phase 5 branch.

Planned steps
1. Create a GitHub Actions workflow to run tests (done).
2. Add targeted tests for transactions and categories endpoints.
3. Add lint/format checks to CI (flake8/black/isort).
4. Add basic Playwright smoke tests (optional / follow-up).
5. Update docs and open PR for branch `feature/phase-5`.

Notes
- The CI workflow uses Postgres 16 and Redis 7 services; `DATABASE_URL` and `REDIS_URL` are set in the job environment.
- If tests require additional setup (seeding, env vars), we'll update the workflow accordingly.
