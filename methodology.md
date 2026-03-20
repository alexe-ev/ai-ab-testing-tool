# Methodology: How prompt-ab Evaluates Prompts

This document explains the evaluation methodology in detail — useful for understanding the approach, reviewing results critically, and adapting the framework to your own use cases.

## The Core Problem

LLM responses are non-deterministic. The same prompt on the same input can produce different outputs. This means you can't evaluate a prompt from a single example — you need a sample, and you need statistics to distinguish signal from noise.

## Evaluation Pipeline

### Step 1: Controlled Experiment

Both prompts are tested on the **same set of inputs** under the **same conditions** (model, temperature, max_tokens). This creates paired data: for each test case, you have response A and response B.

Why paired matters: if one test case is inherently harder than others, both prompts will struggle with it. Paired analysis accounts for this — it looks at the **difference** between A and B on each case, not just the overall means.

### Step 2: LLM-as-Judge (Pointwise)

Each response is scored independently on a 1-5 scale across multiple rubric dimensions. The judge receives:
- The original user question
- The response to evaluate
- The full rubric with anchor descriptions for every score level

Key design decisions:
- **Temperature = 0** for the judge (maximum determinism)
- **Mandatory reasoning** — the judge must explain each score (enables debugging)
- **Anti-bias instructions** — the judge prompt explicitly combats leniency and verbosity bias
- **Full scale usage** — the prompt instructs the judge to use 1-2 for poor responses

### Step 3: LLM-as-Judge (Pairwise)

Both responses are shown to the judge simultaneously. The judge picks a winner (A, B, or tie).

**Swap test**: every pair is evaluated twice with the order reversed. If the judge picks A when A is first, but then picks A-as-B when B is first, the evaluation is marked as consistent. If the result flips, it's flagged as "uncertain" (positional bias detected).

Swap test consistency below 80% indicates the judge prompt needs revision.

### Step 4: Statistical Analysis

**Paired t-test** — tests the null hypothesis "the mean scores are equal." A p-value below 0.05 means we can reject this hypothesis with 95% confidence. We use the paired variant because both prompts answer the same questions.

**Cohen's d (effect size)** — p-value tells you whether the difference is real, but not whether it's meaningful. Cohen's d tells you how large the difference is relative to the variance. Interpretation: 0.2 = small (might not be worth changing), 0.5 = medium (noticeable improvement), 0.8 = large (clear winner).

**Bootstrap confidence intervals** — a non-parametric method for estimating the range of the true mean. We resample 10,000 times and compute the 2.5th and 97.5th percentiles. If the CIs for two prompts don't overlap, the difference is likely real.

**Category breakdown** — aggregate scores per test case category. This reveals cases where Prompt A wins for technical questions but loses for complaints — suggesting you might need different prompts for different scenarios.

## Known Limitations

**LLM-as-judge is not ground truth.** It has biases (positional, verbosity, self-enhancement, leniency). The swap test catches positional bias, and the anti-bias prompt instructions help with others, but human calibration on 20-30 examples is recommended for high-stakes decisions.

**50 test cases is a minimum, not ideal.** It's enough to detect medium effect sizes (d ≥ 0.5) but may miss small but real differences. For fine-grained prompt tuning, use 100+ cases.

**The rubric defines what "better" means.** If your rubric doesn't capture what matters to users, the scores are irrelevant. Always calibrate the rubric against real user feedback before trusting it.

**Temperature > 0 means variance.** If you run the same experiment twice, you'll get slightly different scores. This is expected — the statistical analysis accounts for it. If you need exact reproducibility, set temperature to 0 for the tested prompts as well (though this doesn't reflect real production behavior).
