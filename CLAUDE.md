# prompt-ab-testing

## Stack

**CLI pipeline:**
- Python 3.10+, Click (CLI framework)
- OpenAI SDK, Anthropic SDK (LLM providers)
- scipy, numpy (statistical analysis)
- PyYAML (config parsing)

**Backend (web):**
- FastAPI, SQLAlchemy + SQLite
- httpx (context source HTTP calls)
- Pydantic (API schemas)

**Frontend:**
- Next.js 16, React 19, Tailwind 4
- recharts (trend visualization)

**Deployment:**
- Docker Compose, Caddy (reverse proxy, auto-SSL)
- Multi-stage Dockerfiles

## Structure
```
src/           # CLI pipeline modules (7 modules)
backend/       # FastAPI web backend
  src/api/     # routes, pipeline bridge, CRUD
  src/db/      # SQLAlchemy models, engine, CRUD
  src/         # shared pipeline modules (runner, evaluator, etc.)
  tests/       # 243 backend tests
frontend/      # Next.js web frontend
  src/app/     # pages (experiments, history, compare, settings)
  src/components/  # UI components (experiments, results, ui, layout)
  src/lib/     # types, API client
configs/       # experiment YAML configs (examples, do not modify)
test_sets/     # test case YAML files (examples, do not modify)
rubrics/       # evaluation rubric YAML files (examples, do not modify)
results/       # generated outputs (gitignored)
```

## Commands

**CLI:**
- Install: `pip install -e .`
- Run full pipeline: `prompt-ab run --config configs/example.yaml`
- Dry run: `prompt-ab run --config configs/example.yaml --dry-run`

**Backend:**
- Install: `cd backend && pip install -e ".[dev]"`
- Run: `cd backend && uvicorn src.api.app:app --reload --port 8000`
- Tests: `cd backend && python3 -m pytest -x`
- Lint: `cd backend && ruff check src/`

**Frontend:**
- Install: `cd frontend && npm install`
- Run: `cd frontend && npm run dev`
- Type check: `cd frontend && npx tsc --noEmit`

**Production:**
- `docker compose -f docker-compose.prod.yml up -d`

## Conventions
- Pipeline is linear: runner -> evaluator -> analyzer -> reporter
- Each step produces a JSON file consumed by the next
- LLM abstraction in llm.py: all API calls go through `call_llm()`
- Provider auto-detected from model name prefix (gpt-* / claude-*)
- Retry logic: 3 attempts with exponential backoff on rate limit
- Judge model separate from tested model (default: claude-sonnet)
- Error handling: return dict with `error` key, never raise in API calls
- Frontend dark theme: #0a0a0a bg, #ededed text, borders #222/#333

## Hard rules
- Never commit .env or API keys
- Never modify example configs/test_sets/rubrics (they serve as reference)
- Never hardcode API keys; always read from environment
- Always use `call_llm()` from llm.py for API calls; no direct SDK usage elsewhere
- results/ is gitignored; never commit generated outputs

## Docs
- .claude/docs/architecture.md: pipeline, modules, data flow, web layer
- .claude/docs/domain.md: evaluation methodology, statistics, rubric design

## PR process
- Branch per task: feature/[task-slug]
- PR into main
- No CI gates yet

## Development workflow
- Use /plan to produce the task document. Write it directly into the Linear issue (update description). Don't duplicate in chat, just share the link.
- Use /ship to implement: executor -> qa -> code-reviewer (with retry loop)
- Every task must have tests. No closing a task without test coverage.

## Linear workflow
- Initiative: "AI Agent A/B Testing" (source of truth for project status)
- After completing tasks: update Linear issue status immediately (In Progress / Done / Cancelled)
- After each work session: update initiative description with progress log entry and strike through completed items
- When deferring work ("do later"): create a Linear issue immediately, don't leave it as a conversation note
