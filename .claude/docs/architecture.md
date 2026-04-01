# Architecture

## CLI Pipeline

Linear pipeline, each step produces a JSON file consumed by the next:

```
config.yaml + test_set.yaml + rubric.yaml
  -> runner.py      -> results/run_*.json
  -> evaluator.py   -> results/eval_*.json
  -> analyzer.py    -> results/analysis_*.json
  -> reporter.py    -> results/report_*.md + results/summary_*.json
  -> html_report.py -> results/report_*.html
```

## CLI Modules

| Module | Input | Output | Calls external API |
|--------|-------|--------|--------------------|
| cli.py | CLI args | orchestrates pipeline | no |
| llm.py | system prompt + user input | LLM response + metadata | yes (OpenAI / Anthropic) |
| runner.py | config + test cases | run_*.json (responses from both prompts) | yes (via llm.py) |
| evaluator.py | run_*.json + rubric | eval_*.json (judge scores) | yes (via llm.py, judge model) |
| analyzer.py | eval_*.json | analysis_*.json (statistics) | no |
| reporter.py | analysis_*.json + run_*.json | report_*.md + summary_*.json | no |
| html_report.py | analysis + run + eval JSONs | report_*.html (self-contained) | no |
| context_source.py | context_source config + input | fetched context string | yes (subprocess or HTTP) |

## Web Backend (FastAPI)

```
backend/src/api/
  app.py           # FastAPI app, lifespan, CORS, router registration
  routes.py        # pipeline endpoints: /run, /run-full (SSE), /results
  crud_routes.py   # CRUD: experiments, test sets, rubrics, runs, settings, context source test
  pipeline_bridge.py  # DB entities -> temp YAML -> CLI pipeline execution

backend/src/db/
  engine.py        # SQLite engine, auto-migration (PRAGMA + ALTER TABLE)
  models.py        # SQLAlchemy ORM: Experiment, TestSet, TestCase, Rubric, RubricDimension, Run
  crud.py          # DB queries: list, create, update, delete, with joins and subqueries
```

### Key patterns

- **Pipeline bridge**: `build_config_from_db()` converts DB entities to temp YAML files, then calls the same CLI pipeline functions. This keeps the CLI and web pipelines using identical evaluation logic.
- **SSE streaming**: `run_full_pipeline()` accepts `on_progress` callback. Runner and evaluator emit per-case progress events streamed to frontend via Server-Sent Events.
- **Auto-migration**: `engine.py` checks existing columns via `PRAGMA table_info` and adds new columns with `ALTER TABLE` on startup. No migration framework needed for SQLite.
- **Summary metrics**: Run model stores `summary_metrics` JSON (winner, scores, delta, confidence). Backfilled on startup for existing runs.
- **Iteration chains**: Experiment has `parent_id` self-referential FK. Clone endpoint creates child with incremented version name.

### API structure

- `GET/POST /api/experiments-db/` - experiment CRUD with last_run_metrics
- `POST /api/experiments-db/{id}/run-full` - SSE pipeline execution
- `POST /api/experiments-db/{id}/clone` - clone for iteration
- `GET /api/experiments-db/{id}/chain` - iteration chain
- `GET/POST /api/test-sets/`, `/api/rubrics/` - test set and rubric CRUD
- `GET /api/runs/` - run history with filters, sort, pagination
- `GET /api/runs/compare` - side-by-side run comparison
- `POST /api/context-source/test` - test context source config
- `GET/PUT /api/settings/` - API key management

## Web Frontend (Next.js)

```
frontend/src/app/
  page.tsx                    # experiment list with metric cards + setup checklist
  experiments/[id]/page.tsx   # experiment editor (prompts, config, test set, rubric)
  experiments/[id]/run/page.tsx  # run management, iteration chain, trend chart
  history/page.tsx            # run history table with filters
  history/compare/page.tsx    # side-by-side run comparison
  settings/page.tsx           # API key settings

frontend/src/components/
  experiments/   # experiment-form, prompt-editor, context-source-editor
  results/       # summary-card, score-bars, dimension-table, pairwise-card,
                 # category-breakdown, notable-cases, operational-metrics, response-browser
  test-sets/     # test-set-form, test-case-table
  rubrics/       # rubric-editor
  ui/            # empty-state, setup-checklist, tooltip (shared components)
  layout/        # sidebar navigation
```

### Onboarding patterns

- **Empty states**: all list pages show descriptive guidance when no items exist (EmptyState component)
- **Setup checklist**: Experiments page shows a checklist banner when prerequisites are missing (API keys, test sets, rubrics)
- **Help tooltips**: (?) icons on complex fields (Judge Model, Evaluation Mode, p-value, Cohen's d, swap consistency, etc.)
- **Collapsible sections**: Context Source section collapsed by default in experiment form, expanded if configured

## Context Source Flow

Dynamic context fetching (KN-95 + KN-105):

1. Experiment config may contain `context_source` (script or HTTP), `context_template`, `context_position`
2. `pipeline_bridge.py` propagates these into generated config YAML
3. Runner creates `ContextFetcher` instance if `context_source` present
4. For each test case: static context (from test case) takes priority over dynamic fetch
5. If no static context and fetcher exists: call `fetcher.fetch(input)` with per-input SHA256 caching
6. Context formatted via `context_template` (default: `[Retrieved context]\n{context}\n\n[User question]\n{input}`)
7. Injected into user message or system prompt based on `context_position` (default: user)

## Data flow (CLI)

1. **runner** sends each test case to LLM twice (once per prompt), saves both responses
2. **evaluator** scores each response (pointwise 1-5) and compares pairs (pairwise A/B/tie), runs swap test for positional bias
3. **analyzer** computes paired t-test, Cohen's d, bootstrap CI, category breakdown, recommendation
4. **reporter** formats into markdown + JSON summary
5. **html_report** builds self-contained HTML dashboard with embedded JS viewer

## LLM abstraction (llm.py)

- `detect_provider(model_name)`: auto-detect from prefix (gpt-* = openai, claude-* = anthropic)
- `create_client(provider)`: returns OpenAI() or Anthropic() client
- `call_llm(client, system_prompt, user_input, model, provider, ...)`: unified call with retry (3 attempts, exponential backoff on rate limit)
- API keys loaded from .env via custom dotenv loader (no python-dotenv dependency)

## Config structure

Experiment config references two external YAML files:
- `test_set`: path to test cases YAML
- `rubric`: path to evaluation rubric YAML

Paths are relative to project root.

## Deployment

- `docker-compose.prod.yml`: 3 services (backend, frontend, caddy)
- Backend: multi-stage Dockerfile, uvicorn, health check
- Frontend: 3-stage Dockerfile (deps, build, standalone runner)
- Caddy: reverse proxy, auto-SSL, security headers
- SQLite DB and results persisted via Docker volumes
