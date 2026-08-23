# Project Instructions

> This file supplements (does not replace) the workspace root's `CLAUDE.md` and
> `~/.claude/CLAUDE.md`, both loaded alongside this one. On conflict, priority is:
> **this file > workspace root `CLAUDE.md` > `~/.claude/CLAUDE.md`**.

## Project Overview
Decision-Maker Finder: given only a company website URL (or a list of them), automatically
resolves the company's identity, scrapes its LinkedIn employee list, identifies sales/ownership/GM
decision-makers, validates and enriches their contact info, and surfaces verified contacts
(name, title, LinkedIn, email, phone) in a live-updating UI, exportable to CSV. Replaces a
69-node n8n workflow that required a human to pre-populate company data in a spreadsheet.
Current stage: prototype / initial scaffold.

## Tech Stack
- Language(s): Python 3.11+ (backend), TypeScript (frontend)
- Framework(s): FastAPI (backend), React + Vite (frontend)
- Package manager: pip/venv (backend), npm (frontend)
- Database: SQLite (dev, via `aiosqlite`) — designed to swap to Postgres (`asyncpg`) via
  `DATABASE_URL` for deployment, no code changes required
- Test runner: pytest (backend)
- Linter / formatter: ruff/black (backend), tsc (frontend type checking)
- Deployment target: TBD

## Architecture
- `backend/app/` — FastAPI app, SQLAlchemy models, the async pipeline (`pipeline/`), external API
  clients behind typed interfaces (`integrations/`), REST + WebSocket routers.
- `backend/app/queue.py` — in-process `asyncio.Semaphore`-gated job runner; each submitted URL
  becomes one asyncio task. A failure at any stage marks that job `failed` with the failing
  stage's error and does not block other jobs. An empty result (no qualifying contacts found) is
  not a failure.
- Stage 1 branches the rest of the pipeline on whether a LinkedIn company page was resolved:
  **Path A** (found) scrapes employees (Apify) then classifies each one individually (Claude, one
  call per employee — no separate batch-extraction pass). **Path B** (not found) searches the web
  directly for likely decision-makers (OpenRouter/Sonar; the taxonomy is embedded in the search
  prompt, so there's no separate validation call for this path). Both paths converge at contact
  enrichment. See `backend/app/pipeline/__init__.py` for the full stage list.
- `backend/scripts/init_db.py` — creates tables and seeds the default leadership title taxonomy.
- `frontend/src/` — single-page React app: URL input panel, live job list (WebSocket), expandable
  contacts table, CSV export.
- Data model: `Job` (one per submitted URL) → `Company` (resolved identity) → `Contact`
  (0..N verified decision-makers per company). `Contact.linkedin_url` is nullable — a Path B
  contact with no confirmable LinkedIn profile is enriched via Hunter alone.
- "Campaign A High Risk Workflow" in the source n8n export is the campaign's own internal label
  for its whole pipeline (per its sticky note), not a distinct branch — there's no separate
  risk-scoring logic that was omitted.
- Two separate LLM integrations by design, kept behind independent interfaces so either can be
  swapped alone: OpenRouter/Perplexity Sonar for anything needing live web search + citations
  (Stage 1 identity, Path B decision-maker search), Claude API direct for closed-set
  classification with no search needed (Path A per-employee title check).

## Coding Conventions
- Follow the conventions already present in the codebase over generic style guides.
- Keep functions small and single-purpose; avoid speculative abstractions.
- Match existing naming, file layout, and import style before introducing new patterns.
- Pipeline stages communicate via typed Pydantic models, never loose dicts — each stage's
  input/output contract should be independently testable with fake integration clients.
- See `.claude/rules/` for detailed, path-scoped conventions (code style, testing, API).

## Common Commands
```bash
# Backend: install dependencies
cd backend && python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"

# Backend: init DB (create tables + seed taxonomy)
python scripts/init_db.py

# Backend: run tests
pytest

# Backend: run locally
uvicorn app.main:app --reload

# Frontend: install dependencies
cd frontend && npm install

# Frontend: run locally
npm run dev

# Frontend: type-check + build
npm run build
```

## Important Rules
- Never commit `.env`, secrets, or credentials. Use `.env.example` as the template teammates copy.
- Project secrets (`OPENROUTER_API_KEY`, `APIFY_API_TOKEN`, `ANTHROPIC_API_KEY`, `APOLLO_API_KEY`,
  `HUNTER_API_KEY`, `DATABASE_URL`) live in this project's own `.env` — see `.env.example` for the
  full list. `HUNTER_API_KEY` may be unset; Stage 6 (email fallback) is a complete, swappable stub
  that simply won't succeed until a key is added — this is expected, not a bug.
- Do not accept a LinkedIn company URL unless it can be matched against actual search-result
  citations returned by the Stage 1 LLM call — never let a stage invent one.
- Keep the leadership title taxonomy DB-driven/config-driven, never hardcoded in pipeline logic.
- Ask before installing new dependencies or provisioning cloud/infra resources.
- Do not modify `.claude/settings.json` permissions without calling it out explicitly.
