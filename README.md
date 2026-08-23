# Decision-Maker Finder

Given only a company website URL (or a list of them), this app resolves the company's
identity, scrapes its LinkedIn employee list, identifies sales/ownership/general-management
decision-makers, validates and enriches their contact info, and surfaces verified contacts
(name, title, LinkedIn, email, phone) in a live-updating UI — exportable to CSV. It replaces a
69-node n8n workflow that required a human to pre-populate company data in a spreadsheet.

## Pipeline

Each submitted URL runs through the stages below, independently failable and independently
retried (see `backend/app/queue.py` and `backend/app/pipeline/`). Stage 1 branches the rest of
the pipeline depending on whether a LinkedIn company page could be resolved:

1. **Company Identity Resolution** — site metadata + OpenRouter/Perplexity Sonar (web search),
   with a liveness/parked-domain check and a citation-backed anti-hallucination rule for the
   LinkedIn URL.
   - **Path A — LinkedIn company page found:**
     2. **Employee Scrape** — Apify (`harvestapi/linkedin-company-employees`), requires the
        LinkedIn company URL as input.
     3. **Per-Employee Title Classification** — Claude API, one deterministic Yes/No call per
        scraped employee against the leadership title taxonomy. (No separate batch-extraction
        pass — every employee from the scrape is checked directly.)
   - **Path B — no LinkedIn company page found:**
     3. **Direct Decision-Maker Search** — OpenRouter/Perplexity Sonar searches the web directly
        for likely decision-makers (the taxonomy is embedded in the search prompt itself, so
        there's no separate validation call for this path). A candidate's LinkedIn profile is
        only accepted if citation-backed, same rule as Stage 1.
5. **Contact Enrichment** — Apollo.io `/people/match`, keyed by LinkedIn URL. A candidate with no
   LinkedIn profile (only possible via Path B) skips Apollo entirely.
6. **Email Fallback** — Hunter.io `emailFinder`/`emailVerifier`. For a contact with a LinkedIn
   URL, this is non-fatal and just leaves the email blank if it fails or `HUNTER_API_KEY` is
   unset. For a Path B contact with **no** LinkedIn URL, Hunter is the only possible source of an
   email — if it can't find one, the contact is discarded here.
7. **Normalize** — phone digits-only, name casing.
8. **Dedup** — skip contacts that already exist by Apollo ID or LinkedIn URL.
9. **Persist + Surface** — write `Contact` rows, mark the job `done`, broadcast over WebSocket.

A failure at any stage marks that job `failed` with the stage name and error, and never blocks
other jobs — each submitted URL runs as its own concurrency-limited `asyncio` task. An empty
result (no qualifying employees, or no candidates found via direct search) is not a failure —
the job just completes with zero contacts.

> **Note on "High Risk":** the source n8n export's sticky note labels its entire lead-gen
> pipeline "Campaign A High Risk Workflow" — that's the campaign's own internal codename, not a
> distinct conditional branch. There's no separate risk-scoring logic that was omitted.

## Setup

### Environment variables

Copy `.env.example` to `.env` and fill in real values:

| Variable | Used by | Required? |
|---|---|---|
| `OPENROUTER_API_KEY` | Stage 1 identity + Path B direct decision-maker search (Perplexity Sonar) | Yes |
| `APIFY_API_TOKEN` | Path A employee scrape | Yes |
| `ANTHROPIC_API_KEY` | Path A per-employee title classification (Claude) | Yes |
| `APOLLO_API_KEY` | Stage 5 (contact enrichment) | Yes |
| `HUNTER_API_KEY` | Stage 6 (email fallback) | No — stage degrades gracefully if unset |
| `DATABASE_URL` | Database connection | No — defaults to local SQLite |

`.env` is gitignored; never commit real key values.

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Create tables + seed the default leadership title taxonomy
python scripts/init_db.py

# Run tests (uses fake integration clients — no API keys needed)
pytest

# Lint
ruff check app scripts tests

# Run the API server (http://localhost:8000)
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install

# Type-check + build
npm run build

# Run the dev server (http://localhost:5173, proxies /jobs, /companies, /ws to :8000)
npm run dev
```

Open http://localhost:5173, paste one or more website URLs into the textarea, and submit.
Batches of more than `BATCH_CONFIRMATION_THRESHOLD` (default 10) URLs return a cost estimate
that requires explicit confirmation before any jobs are enqueued.

## Database

SQLite is used for local development (`DATABASE_URL=sqlite+aiosqlite:///./decision_maker_finder.db`
by default). The schema (`backend/app/models.py`) uses async SQLAlchemy 2.0, so switching to
Postgres for deployment is a `DATABASE_URL` change (`postgresql+asyncpg://...`) plus installing
`asyncpg` — no code changes required. `scripts/init_db.py` creates tables via SQLAlchemy metadata;
for a real Postgres deployment, introduce Alembic migrations before that first deploy (not set up
in this scaffold).

## Swapping an external API provider

Every provider sits behind a typed `Protocol` in `backend/app/integrations/base.py`:
`SearchLLMClient` (Stage 1 identity + Path B decision-maker search — needs web search),
`EmployeeScraperClient` (Path A employee scrape), `ClassifierLLMClient` (Path A per-employee
classification — no web search needed), `ContactEnrichmentClient` (Stage 5), `EmailFinderClient`
(Stage 6). Swapping a provider means writing a new class that satisfies the relevant Protocol
and wiring it into `backend/app/queue.py` — no other pipeline code changes.

## Leadership title taxonomy

Stored in the `title_taxonomy` DB table (seeded from `backend/app/taxonomy.py`'s
`DEFAULT_TAXONOMY_SEED`). Default categories: `ownership` (CEO/owner/founder/partner), `cxo`
(CFO/COO/CTO/CMO/etc.), `director` (Director/Managing Director/VP), and `department_head`
(Head of Sales/Marketing/Operations/etc.) — general-purpose, not tied to any one vertical. Edit
rows directly (or `is_active=false` to retire a title) or extend the seed list — pipeline code
never hardcodes titles. `seed_default_taxonomy()` only *adds* missing labels on startup; it never
removes or deactivates existing rows, so changing `DEFAULT_TAXONOMY_SEED` only affects fresh
databases — on an existing DB, deactivate stale rows manually (set `is_active = false` for labels
no longer in the seed) before restarting.
