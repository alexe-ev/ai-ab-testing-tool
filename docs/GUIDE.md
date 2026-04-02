# How to use prompt-ab

Step-by-step guide for running an A/B test on two system prompts.

Two ways to work: **Web UI** (recommended) and **CLI** (for automation and CI).

---

## What it does

Takes two system prompts, runs both through a set of test cases, evaluates responses via LLM-as-judge, computes statistics, and generates a report. Output: which prompt is better, by how much, and whether you can trust that conclusion.

---

## Prerequisites

Python 3.10+. Node.js 18+ (for Web UI). An OpenAI or Anthropic API key.

You only need the provider you're using. Provider is auto-detected from model name: `gpt-*` = OpenAI, `claude-*` = Anthropic.

---

# Web UI

## Quick Start

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn src.api.app:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. API keys can be entered on the Settings page.

## Working in the Web UI

### 1. Create an experiment

Home page > "New Experiment". Fill in:
- Name and description
- Two variants: system prompt + model for each
- Judge model

**Two testing modes:**
- **Different prompts, same model:** classic prompt A/B test. One model, two system prompts.
- **Different models, same prompt:** cross-model comparison. Same prompt, but variant A on gpt-4o-mini, variant B on claude-sonnet. Each variant can have its own model, temperature, and max_tokens.

### 2. Create test cases

Test Sets page > "New Test Set".
- Add cases one by one via form
- Or bulk import from YAML/CSV
- Each case: input (required), category, context (optional), reference

### 3. Create a rubric

Rubrics page > "New Rubric".
- Pick a template (Support, Content, Code) or start from scratch
- Add dimensions with weights (sum = 1.0)
- Each dimension: 5 levels with descriptions

### 4. Run the experiment

Experiment page > "Run". Select test set, rubric, judge model. Click "Run".
- Dry run: validate config without API calls
- Full run: complete pipeline with live log (SSE streaming)
- Progress visible in real-time: case X of Y, timer

### 5. View results

After completion, a dashboard opens:
- Summary card: winner, confidence, recommendation
- Score bars: visual comparison of average scores
- Dimension table: p-values, Cohen's d, delta per dimension
- Pairwise win rates: direct win percentage with swap consistency
- Category breakdown: results by category (split detection)
- Response browser: responses side by side, judge scores with reasoning

### 6. Iterate

"Clone & Iterate" creates a copy of the experiment linked to its predecessor. The iteration chain (v1 > v2 > v3) is displayed on the run page alongside a trend chart.

### 7. Compare runs

History > select two runs with checkboxes > "Compare". Shows both results side by side with delta per dimension.

## Context Source (RAG)

For testing RAG prompts where each test case needs context from a retrieval pipeline:

**Static context:** add a `context` field to the test case. Both prompts receive the same context.

**Dynamic context:** configure in the experiment (section "Context Source"):

*Script:*
```
python my_rag.py --query '{input}'
```
Executes the command, substituting the test case input. stdout = context.

*HTTP:*
```
POST https://my-api.com/retrieve
Body: {"query": "{input}", "top_k": 5}
Response path: data.context
```
Calls the API, substituting input. Extracts context via dot-path from the response.

The "Test" button validates config without running the experiment.

**Priority:** static context in the test case always overrides dynamic context.

**Injection template:** the "Context Injection Format" section lets you configure the format (`{context}` and `{input}` placeholders) and position (user message or system prompt).

## Production Deployment

```bash
cp .env.example .env
# Fill in DOMAIN, OPENAI_API_KEY, ANTHROPIC_API_KEY

docker compose -f docker-compose.prod.yml up -d
```

Caddy automatically obtains an SSL certificate. Details in `DEPLOY.md`.

---

# CLI

## Setup

```bash
cd prompt-ab-testing
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Add your key to `.env`:

```
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...
```

---

## Step 1. Create an experiment config

Create a file in `configs/`, e.g. `configs/my_experiment.yaml`:

```yaml
experiment:
  name: "my-experiment"
  description: "What you're testing and why."
  hypothesis: "What you expect to see."

model:
  name: "gpt-4o-mini"       # default model
  temperature: 0.3
  max_tokens: 1024

prompts:
  prompt_a:
    name: "Current"          # short label for the report
    system: |
      Your current system prompt.

  prompt_b:
    name: "New"
    system: |
      The new version you want to test.

test_set: "test_sets/my_cases.yaml"
rubric: "rubrics/my_rubric.yaml"

output:
  dir: "results"
  formats: ["markdown", "json"]
```

**Per-prompt model override** for cross-model comparison:

```yaml
model:
  name: "gpt-4o-mini"       # fallback if prompt has no model
  temperature: 0.3
  max_tokens: 1024

prompts:
  prompt_a:
    name: "GPT-4o-mini"
    system: |
      Same prompt for both.
    model:                   # overrides the global model
      name: "gpt-4o-mini"
      temperature: 0.3

  prompt_b:
    name: "Claude Sonnet"
    system: |
      Same prompt for both.
    model:
      name: "claude-sonnet-4-20250514"
      temperature: 0.3
```

If a prompt has a `model` block, it's used instead of the global one. You can override just the model, just the temperature, or everything.

**Important:** change one variable at a time. If you change both the prompt and the model, you won't know what made the difference.

Working example: `configs/example.yaml`.

---

## Step 2. Create test cases

A file in `test_sets/`, e.g. `test_sets/my_cases.yaml`:

```yaml
test_cases:
  - id: "billing-001"
    category: "billing"
    input: "I was charged twice for my subscription this month. I need a refund."

  - id: "technical-001"
    category: "technical"
    input: "The PDF export button doesn't work. I click it and nothing happens. Chrome, Mac."

  - id: "complaint-001"
    category: "complaint"
    input: "Your product crashed three times this month. We pay $500/mo, this is unacceptable."
```

**How many cases:**
- 5: only to verify the pipeline works, statistics are meaningless
- 30: minimum for real analysis
- 50+: recommended

**Categories:** cover the real scenarios your product sees. Categories let you spot splits: prompt B may win overall but lose on technical questions.

Working examples: `test_sets/support_5.yaml`, `test_sets/support_50.yaml`.

---

## Step 3. Create an evaluation rubric

A file in `rubrics/`, e.g. `rubrics/my_rubric.yaml`:

```yaml
dimensions:
  - name: "accuracy"
    weight: 0.40
    description: "Is the information factually correct?"
    levels:
      - score: 5
        description: "Fully correct, includes caveats and edge cases."
      - score: 4
        description: "Correct. Minor omissions that don't affect the outcome."
      - score: 3
        description: "Mostly correct, but some inaccuracies that could confuse."
      - score: 2
        description: "Partially correct. Could lead to wrong actions."
      - score: 1
        description: "Contains errors that would lead to wrong user actions."

  - name: "actionability"
    weight: 0.30
    description: "Can the user take concrete action based on this response?"
    levels:
      - score: 5
        description: "Clear numbered steps. User knows exactly what to do and in what order."
      - score: 4
        description: "Good guidance. User can act with minimal clarification."
      - score: 3
        description: "General direction exists, no concrete steps."
      - score: 2
        description: "Vague advice. Unclear what to do."
      - score: 1
        description: "Nothing actionable. User is stuck."

  - name: "tone"
    weight: 0.30
    description: "Is the tone appropriate?"
    levels:
      - score: 5
        description: "Warm and professional. Customer feels heard."
      - score: 4
        description: "Professional and polite."
      - score: 3
        description: "Neutral. Transactional but not bad."
      - score: 2
        description: "Robotic or slightly dismissive."
      - score: 1
        description: "Rude or inappropriate tone."
```

**Tips:**
- Weights should sum to 1.0
- Level descriptions should be concrete. "Good response" is useless. "Includes numbered steps" works.
- 3-5 dimensions is optimal. More and the judge gets less precise.
- All 5 levels must be filled in.

Working example: `rubrics/support.yaml`.

---

## Step 4. Run the test

First, validate the pipeline on 5 cases:

```bash
prompt-ab run --config configs/test_5.yaml
```

If everything passes, run the full experiment:

```bash
prompt-ab run --config configs/my_experiment.yaml
```

Result files appear in `results/`.

**Cost estimates** (for 50 cases, excluding the judge):
- `gpt-4o-mini`: ~$1-2, ~10 minutes
- `gpt-4o` / Claude Sonnet: ~$3-5
- Judge `gpt-5.4` adds ~$2-5 on top (60 calls for 15 cases in both mode)

---

## Step 5. Read the results

Open the HTML dashboard in a browser:

```bash
open results/report_*.html
```

What to look for:

**Dimension table**
Which prompt won on each rubric dimension. p-value and effect size next to each.

**p-value**: if < 0.05, the difference is statistically significant (not random).

**Effect size (Cohen's d)**:
- < 0.2: negligible, not worth switching
- 0.2-0.5: small, switch only if it's a high-stakes prompt
- 0.5-0.8: medium, worth switching
- 0.8+: large, definitely switch

**Head-to-head win rate**: how many direct comparisons prompt B won. 70%+ is a strong signal.

**Swap consistency**: should be 80%+. If lower, the judge has positional bias (tends to favor whichever response comes first). Try a stronger judge model.

**Category breakdown**: you may find that B wins overall but A handles technical questions better. That's a reason to use different prompts for different query types.

---

## Additional commands

**Dry run** (preview without API calls):
```bash
prompt-ab run --config configs/my_experiment.yaml --dry-run
```

**Choosing models:**

- **Tested model** should match what you run in production. Testing a prompt for `gpt-4o-mini` in prod? Use `gpt-4o-mini` in config. Otherwise results don't transfer.
- **Judge** should be a flagship model with reasoning support. Currently that's `gpt-5.4` (OpenAI) or `claude-opus-4-6` (Anthropic). A judge weaker than the tested model is unreliable.

```bash
prompt-ab run --config configs/my_experiment.yaml --judge-model gpt-5.4
```

**Re-evaluate without re-generating responses** (if you changed the rubric):
```bash
# Important: specify the exact run file path, otherwise it may pick up the wrong one:
prompt-ab evaluate --results results/run_my-experiment_XXXXXX.json --rubric rubrics/new_rubric.yaml
```

**Run individual steps** (specify exact files, not globs):
```bash
prompt-ab evaluate --results results/run_my-experiment_XXXXXX.json --rubric rubrics/my_rubric.yaml --judge-model gpt-5.4
prompt-ab analyze --eval results/eval_my-experiment_XXXXXX.json
prompt-ab report --analysis results/analysis_my-experiment_XXXXXX.json --run results/run_my-experiment_XXXXXX.json --eval results/eval_my-experiment_XXXXXX.json
```

---

## What's in the results/ folder

| File | Contents |
|------|----------|
| `run_*.json` | Raw responses from both prompts |
| `eval_*.json` | Judge scores for every response |
| `analysis_*.json` | Statistical analysis |
| `report_*.html` | Interactive dashboard |
| `report_*.md` | Markdown report |
| `summary_*.json` | Compact JSON for automation |

### summary.json structure (for automation / agents)

```json
{
  "run_id": "my-experiment_20260319_...",
  "prompt_a": "Current",
  "prompt_b": "New",
  "recommendation": "New",
  "confidence": "high",
  "overall_score_a": 3.98,
  "overall_score_b": 4.15,
  "win_rate_a": 0.43,
  "win_rate_b": 0.45,
  "swap_consistency": 0.84,
  "dimensions": {
    "accuracy": {
      "score_a": 4.02,
      "score_b": 4.10,
      "p_value": 0.55,
      "effect_size": -0.09
    }
  }
}
```

Read the output without a browser:
```bash
cat results/summary_*.json | python3 -m json.tool
```

---

## Running from an agent

Minimal set of actions for autonomous execution:

1. Create three files: `configs/NAME.yaml`, `test_sets/NAME.yaml`, `rubrics/NAME.yaml`
2. Run a dry run to validate config: `prompt-ab run --config configs/NAME.yaml --dry-run`
3. Run the full pipeline with an explicit judge: `prompt-ab run --config configs/NAME.yaml --judge-model gpt-5.4`
4. Read the result: `cat results/summary_NAME_*.json`
5. Interpret: `recommendation` = winner, `confidence` = certainty, `dimensions` = per-dimension breakdown

Rules for agents:
- Always specify `--judge-model` explicitly. The default requires an Anthropic key.
- Don't use `--eval-only` without an explicit path to the run file (`--results results/run_NAME_*.json`). Otherwise it picks up the latest file in the folder, which may belong to a different experiment.
- Minimum 30 cases for meaningful statistics. Fewer cases will run, but p-values are meaningless.
- When interpreting effect_size: a negative value means B is better than A.

---

## When you can't trust the results

- Fewer than 30 cases: statistics are unreliable
- Swap consistency < 80%: the judge has positional bias
- More than one variable changed between prompts: unclear what actually made the difference
- Rubric doesn't reflect real product priorities: high scores don't equal a good prompt
- Test cases don't cover the actual distribution of queries: results don't transfer to production
