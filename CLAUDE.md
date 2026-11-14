# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

ML Code Trainer is a learning app for writing, running and reading ML-flavoured Python. The frontend is React 19 + TypeScript + Vite, with Monaco as the editor and Pyodide running Python in the browser. The backend is FastAPI with SQLAlchemy: SQLite in development and PostgreSQL/Supabase in production. The curriculum is authored as Python and JSON under `content/` and compiled into versioned JSON catalogs. The README, the docs and the lesson text are written in Japanese.

Toolchain: Node 24, Python 3.12+ (CI uses 3.13), and `uv`. Run every command from the repo root. The primary dev shell is Windows PowerShell.

## Commands

```powershell
npm ci
uv sync --project apps/api --frozen --python 3.13
Copy-Item .env.example .env

# Dev servers (two terminals). Vite proxies /api to API_PROXY_TARGET, default :8000
uv run --project apps/api python -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port 8000
npm run dev          # http://127.0.0.1:5173

# Frontend (npm workspace apps/web)
npm run lint; npm run typecheck; npm run test; npm run build
npm run test -- src/features/answer.test.ts        # one Vitest file

# Backend / content
uv run --project apps/api ruff check --config apps/api/pyproject.toml apps/api content scripts
uv run --project apps/api python -m pytest apps/api/tests -q
uv run --project apps/api python -m pytest apps/api/tests/test_combining.py -q   # one file (append ::test_name for one test)
uv run --project apps/api python scripts/compile_content.py      # regenerate content/compiled/*
uv run --project apps/api python scripts/validate_content.py     # full native validation, both seeds
uv run --project apps/api python scripts/validate_content.py --concept NP07
uv run --project apps/api python scripts/check_security.py

# API contract: after changing API schemas, regenerate both files and commit them (CI fails on a diff)
uv run --project apps/api python scripts/export_openapi.py; npm run api:types

# E2E (Playwright, Chromium)
npx playwright install chromium
npm run test:e2e
npx playwright test -c playwright.concrete.config.ts arguments.spec.ts   # one spec
npm run test:browser-content   # all problems run through the real Pyodide path; slow (10+ min)
```

The E2E setup:
- All Playwright configs inherit from `playwright.concrete.config.ts`. It starts its own Vite server on :5174 and its own API on :8001, against an isolated SQLite DB under `artifacts/concrete-drill/`. Your dev `trainer.db` and dev servers are not touched.
- The configured API is launched with `apps/api/.venv/Scripts/python.exe` (or `bin/python` on Linux), so run `uv sync` first.
- The other configs only narrow `testMatch`: `phase1`, `runtime` (performance profiling) and `unified`.

CI (`.github/workflows/ci.yml`) runs everything above except `test:browser-content`, and also runs `npm audit --audit-level=high`.

## Architecture

### Content pipeline (most edits land here)
- **Authoring.** `content/catalog.py` is the base catalog. Each ordered concept (PY01–PY03, NP01–NP08) is a pair of files:
  - `content/<topic>.json` holds the final wording, display examples, hints and reference solutions.
  - `content/<topic>.py` holds the fixtures, alternate inputs and grading rules. It exports `CONCEPT_ID`, `LESSONS` and `compile_<topic>(concept, seed)`.
- **Registration.** A new concept must be registered in `ORDERED_LESSONS` in `scripts/compile_content.py`. Its fixture generator must also be added in `scripts/validate_content.py`. Problem totals are hard-coded in several places and must be bumped together:
  - the format-distribution `Counter` in `validate_content.py`
  - `apps/api/tests/test_concrete.py` and `test_continuation.py`
  - `tests/e2e/trainer.spec.ts` (the "Drill N" link)
  - the README and `docs/CONTENT_GUIDE.md`
- **Compiling.** `scripts/compile_content.py` writes these files to `content/compiled/`:
  - `private.json` (seed 42, includes solutions and hidden tests)
  - `variant-99.json` (seed 99)
  - `public.json` (stripped)
  - `display.json` (tuple/type display sidecar, keyed `version_id:seed`)
  - `manifest.json`
  Treat `content/compiled/` as generated output; never hand-edit it.
- **Versioning.** IDs follow `version_id = "<id>@<content_version>"`. Once a problem has shipped, any change to it requires a version bump. Before bumping, snapshot the old catalogs into `content/versions/vN-<topic>-seed{42,99}.json`. `validate_content.py` fails if an existing `(version_id, seed)` changes without a bump, and the API serves archived versions by exact ID.
- **Hierarchy.** Module → Concept → Family → Version → Variant (seed). Seeds are never counted as extra problems.
- **Private material.** Never copy private catalogs (solutions, hidden tests) into the web build or any public payload.

### Grading and execution
- **Shared runner.** `content/runner.py` runs a problem's test cases and checks the code's syntax tree (AST) for required calls and options. It is shared by native validation and the trusted grading path.
- **Browser runs.** The browser runs only public tests, inside an opaque-origin sandbox iframe with a Pyodide Worker (`apps/web/src/features/python*.{ts,js}`). These results are saved as `browser_provisional` and never count as mastery. Credentials must never reach the iframe or Worker.
- **Official grading.** The API creates a job, and a separate worker process (`apps/api/app/worker.py`) sends only inputs and code to a Modal sandbox. Expected values and comparison stay on the trusted side (`grading.py`, `execution.py`). With `EXECUTION_PROVIDER=disabled` (the local default), sandbox-only problems such as PyTorch show an explicit "unavailable" error instead of falling back. Never add a local-exec fallback: `check_security.py` forbids `exec` in the API.

### Backend (`apps/api/app/`)
- `main.py` contains every route, under `/api/v1`.
- `content.py` loads the compiled catalogs and archived versions at import time.
- `learning.py` holds progression and spaced review: Guided → Partial → Independent gates, and review intervals of 1/3/7/14/30 days (`interval-v1`).
- `auth.py` handles two modes: a local guest via an HttpOnly cookie, or a verified Supabase JWT.
- Locally, `trainer.db` is read straight from the compiled catalog. `scripts/seed_content.py` syncs content into PostgreSQL only. Migrations are in `supabase/migrations/`.

### Frontend (`apps/web/src/`)
- TanStack Query manages server state.
- Zustand (`lib/store.ts`) persists only UI preferences: focus mode, split sizes and the result tab.
- Drafts are saved in IndexedDB per user and synced to the API with revision checks (`features/useDraft.ts`, `lib/drafts.ts`). On a conflict the local code must be kept.
- `types/api.d.ts` is generated from `apps/api/openapi.json`.

## Docs worth reading before larger changes
- `docs/ARCHITECTURE.md`: runtime isolation, grading, and the learning model
- `docs/CONTENT_GUIDE.md` and `docs/CONTENT_STYLE_GUIDE.md`: per-concept grading rules and authoring conventions
- `docs/TESTING.md`: what each check covers, and which tests need live Supabase or Modal credentials (`RLS_TEST_DATABASE_URL`, `RUN_LIVE_MODAL_TESTS=1`)
