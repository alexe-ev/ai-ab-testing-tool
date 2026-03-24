"""
Analyzer: statistical analysis of evaluation results.

Pipeline: eval_XXX.json → Analyzer → analysis_XXX.json

Computes: means, std, paired t-test, Cohen's d, bootstrap CI,
win rate, breakdown by category, best/worst cases.
"""

import json
from pathlib import Path
from datetime import datetime, timezone

import numpy as np
from scipy import stats

from src.pricing import calculate_cost


# ─── Core statistics ──────────────────────────────────────────────

def paired_ttest(scores_a: list[float], scores_b: list[float]) -> dict:
    """
    Paired t-test: are the means significantly different?
    Uses paired test because both prompts answer the SAME test cases.
    """
    if len(scores_a) < 3 or len(scores_b) < 3:
        return {"t_statistic": None, "p_value": None, "note": "Too few samples"}

    t_stat, p_value = stats.ttest_rel(scores_a, scores_b)
    return {
        "t_statistic": round(float(t_stat), 4),
        "p_value": round(float(p_value), 4),
        "significant_005": bool(p_value < 0.05),
        "significant_010": bool(p_value < 0.10),
    }


def cohens_d(scores_a: list[float], scores_b: list[float]) -> float | None:
    """
    Effect size: how LARGE is the difference (not just significant).
    0.2 = small, 0.5 = medium, 0.8 = large.
    """
    a, b = np.array(scores_a), np.array(scores_b)
    n_a, n_b = len(a), len(b)
    if n_a < 2 or n_b < 2:
        return None
    var_a = np.var(a, ddof=1)
    var_b = np.var(b, ddof=1)
    pooled_std = np.sqrt(((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2))
    if pooled_std == 0:
        return 0.0
    return round(float((np.mean(a) - np.mean(b)) / pooled_std), 4)


def interpret_effect_size(d: float | None) -> str:
    """Human-readable interpretation of Cohen's d."""
    if d is None:
        return "insufficient data"
    abs_d = abs(d)
    if abs_d < 0.2:
        return "negligible"
    elif abs_d < 0.5:
        return "small"
    elif abs_d < 0.8:
        return "medium"
    else:
        return "large"


def bootstrap_ci(
    scores: list[float],
    n_bootstrap: int = 10000,
    ci: float = 0.95,
) -> dict:
    """
    Bootstrap confidence interval for the mean.
    Non-parametric — no assumptions about distribution shape.
    """
    if len(scores) < 3:
        return {"lower": None, "upper": None, "mean": None}

    arr = np.array(scores)
    means = np.array([
        np.mean(np.random.choice(arr, size=len(arr), replace=True))
        for _ in range(n_bootstrap)
    ])

    alpha = (1 - ci) / 2
    lower = float(np.percentile(means, alpha * 100))
    upper = float(np.percentile(means, (1 - alpha) * 100))

    return {
        "mean": round(float(np.mean(arr)), 4),
        "lower": round(lower, 4),
        "upper": round(upper, 4),
        "ci_level": ci,
    }


# ─── Score extraction ─────────────────────────────────────────────

def extract_pointwise_scores(evaluations: list[dict], key: str, dimension: str) -> list[float]:
    """
    Extract scores for a specific prompt and dimension.
    Skips None/missing scores.
    """
    scores = []
    for e in evaluations:
        if e.get("skipped"):
            continue
        pw = e.get("pointwise", {})
        prompt_scores = pw.get(key, {})
        dim_data = prompt_scores.get(dimension, {})
        score = dim_data.get("score")
        if score is not None:
            scores.append(float(score))
    return scores


def extract_pairwise_results(evaluations: list[dict]) -> list[dict]:
    """Extract pairwise results (winner, consistency) from evaluations."""
    results = []
    for e in evaluations:
        if e.get("skipped"):
            continue
        pw = e.get("pairwise")
        if pw:
            results.append({
                "test_case_id": e["test_case_id"],
                "category": e["category"],
                "winner": pw.get("winner"),
                "consistent": pw.get("consistent"),
            })
    return results


# ─── Operational metrics ──────────────────────────────────────────

def compute_operational_metrics(run_data: dict) -> dict:
    """
    Compute per-prompt operational metrics: model, latency, tokens, cost.

    Returns a dict with per-prompt stats and a multi_variable_warning flag.
    """
    config = run_data.get("config", {})
    prompt_models = config.get("prompt_models", {})
    prompt_names = config.get("prompt_names", {})
    results = run_data.get("results", [])

    prompt_keys = list(prompt_models.keys()) if prompt_models else []

    per_prompt: dict[str, dict] = {}

    for key in prompt_keys:
        model = prompt_models.get(key, "unknown")
        latencies = []
        total_input = 0
        total_output = 0
        n = 0

        for r in results:
            resp = r.get("responses", {}).get(key, {})
            if resp.get("error"):
                continue
            lat = resp.get("latency_seconds")
            if lat is not None:
                latencies.append(float(lat))
            inp = resp.get("input_tokens", 0) or 0
            out = resp.get("output_tokens", 0) or 0
            total_input += inp
            total_output += out
            n += 1

        total_tokens = total_input + total_output
        cost = calculate_cost(model, total_input, total_output)

        lat_avg = round(float(np.mean(latencies)), 3) if latencies else None
        lat_p50 = round(float(np.percentile(latencies, 50)), 3) if latencies else None
        lat_p95 = round(float(np.percentile(latencies, 95)), 3) if latencies else None
        avg_tokens = round(total_tokens / n, 1) if n > 0 else None

        per_prompt[key] = {
            "name": prompt_names.get(key, key),
            "model": model,
            "n_responses": n,
            "latency": {
                "avg": lat_avg,
                "p50": lat_p50,
                "p95": lat_p95,
            },
            "tokens": {
                "total_input": total_input,
                "total_output": total_output,
                "total": total_tokens,
                "avg_per_response": avg_tokens,
            },
            "cost_usd": cost,
        }

    # Multi-variable warning: both prompt texts AND models differ
    prompt_keys_list = list(prompt_keys)
    multi_variable_warning = False
    if len(prompt_keys_list) >= 2:
        key_a, key_b = prompt_keys_list[0], prompt_keys_list[1]
        model_a = prompt_models.get(key_a)
        model_b = prompt_models.get(key_b)
        # Warning when models differ (run_data does not store prompt text,
        # so model difference is the detectable multi-variable signal).
        multi_variable_warning = model_a != model_b

    return {
        "per_prompt": per_prompt,
        "multi_variable_warning": multi_variable_warning,
    }


def _load_run_data(eval_data: dict, run_path: str | None, output_dir: str) -> dict | None:
    """
    Try to load the run JSON file.
    Uses run_path if provided; otherwise searches output_dir for run_{run_id}.json.
    Returns None if not found (graceful degradation).
    """
    if run_path:
        try:
            with open(run_path) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return None

    run_id = eval_data.get("run_id")
    if run_id:
        candidate = Path(output_dir) / f"run_{run_id}.json"
        if candidate.exists():
            try:
                with open(candidate) as f:
                    return json.load(f)
            except (OSError, json.JSONDecodeError):
                return None

    return None


# ─── Main analysis ────────────────────────────────────────────────

def analyze_evaluation(eval_path: str, output_dir: str = "results", run_path: str | None = None) -> str:
    """
    Full statistical analysis of evaluation results.
    Returns path to analysis JSON.

    run_path: optional path to run_*.json for operational metrics.
    If not provided, tries to find it automatically next to the eval file.
    """
    with open(eval_path) as f:
        eval_data = json.load(f)

    config = eval_data["config"]
    key_a = config["prompt_a"]["key"]
    key_b = config["prompt_b"]["key"]
    name_a = config["prompt_a"]["name"]
    name_b = config["prompt_b"]["name"]

    evaluations = eval_data["evaluations"]
    rubric = eval_data.get("rubric", {})
    dimensions = [d["name"] for d in rubric.get("dimensions", [])]
    weights = {d["name"]: d.get("weight", 1.0) for d in rubric.get("dimensions", [])}

    analysis = {
        "prompt_a": {"key": key_a, "name": name_a},
        "prompt_b": {"key": key_b, "name": name_b},
    }

    # ── Pointwise analysis ──
    if any(e.get("pointwise") for e in evaluations if not e.get("skipped")):
        dim_analysis = {}

        for dim in dimensions:
            scores_a = extract_pointwise_scores(evaluations, key_a, dim)
            scores_b = extract_pointwise_scores(evaluations, key_b, dim)

            if not scores_a or not scores_b:
                continue

            d = cohens_d(scores_a, scores_b)

            dim_analysis[dim] = {
                "weight": weights.get(dim, 1.0),
                name_a: {
                    "mean": round(float(np.mean(scores_a)), 3),
                    "std": round(float(np.std(scores_a, ddof=1)), 3),
                    "n": len(scores_a),
                    "ci_95": bootstrap_ci(scores_a),
                },
                name_b: {
                    "mean": round(float(np.mean(scores_b)), 3),
                    "std": round(float(np.std(scores_b, ddof=1)), 3),
                    "n": len(scores_b),
                    "ci_95": bootstrap_ci(scores_b),
                },
                "comparison": {
                    "mean_diff": round(float(np.mean(scores_a) - np.mean(scores_b)), 3),
                    "ttest": paired_ttest(scores_a, scores_b),
                    "cohens_d": d,
                    "effect_interpretation": interpret_effect_size(d),
                    "better": name_a if np.mean(scores_a) > np.mean(scores_b) else name_b,
                },
            }

        # Weighted overall score
        overall_a, overall_b, total_weight = 0.0, 0.0, 0.0
        for dim, data in dim_analysis.items():
            w = data["weight"]
            overall_a += data[name_a]["mean"] * w
            overall_b += data[name_b]["mean"] * w
            total_weight += w

        if total_weight > 0:
            overall_a /= total_weight
            overall_b /= total_weight

        analysis["pointwise"] = {
            "dimensions": dim_analysis,
            "overall_weighted": {
                name_a: round(overall_a, 3),
                name_b: round(overall_b, 3),
                "better": name_a if overall_a > overall_b else name_b,
            },
        }

        # ── Category breakdown ──
        categories = set(e["category"] for e in evaluations if not e.get("skipped"))
        if len(categories) > 1:
            cat_breakdown = {}
            for cat in sorted(categories):
                cat_evals = [e for e in evaluations if e.get("category") == cat and not e.get("skipped")]
                cat_scores_a = []
                cat_scores_b = []
                for dim in dimensions:
                    sa = extract_pointwise_scores(cat_evals, key_a, dim)
                    sb = extract_pointwise_scores(cat_evals, key_b, dim)
                    cat_scores_a.extend(sa)
                    cat_scores_b.extend(sb)

                if cat_scores_a and cat_scores_b:
                    cat_breakdown[cat] = {
                        "n_cases": len(cat_evals),
                        name_a: round(float(np.mean(cat_scores_a)), 3),
                        name_b: round(float(np.mean(cat_scores_b)), 3),
                        "better": name_a if np.mean(cat_scores_a) > np.mean(cat_scores_b) else name_b,
                    }

            analysis["category_breakdown"] = cat_breakdown

    # ── Pairwise analysis ──
    pairwise_results = extract_pairwise_results(evaluations)
    if pairwise_results:
        total_pw = len(pairwise_results)
        wins_a = sum(1 for r in pairwise_results if r["winner"] == "A")
        wins_b = sum(1 for r in pairwise_results if r["winner"] == "B")
        ties = sum(1 for r in pairwise_results if r["winner"] == "TIE")
        uncertain = sum(1 for r in pairwise_results if r["winner"] == "UNCERTAIN")
        consistent = sum(1 for r in pairwise_results if r.get("consistent"))

        # Win rate (excluding uncertain)
        decided = wins_a + wins_b + ties
        win_rate_a = round(wins_a / decided, 3) if decided > 0 else None
        win_rate_b = round(wins_b / decided, 3) if decided > 0 else None

        analysis["pairwise"] = {
            "total": total_pw,
            f"wins_{name_a}": wins_a,
            f"wins_{name_b}": wins_b,
            "ties": ties,
            "uncertain": uncertain,
            f"win_rate_{name_a}": win_rate_a,
            f"win_rate_{name_b}": win_rate_b,
            "swap_test_consistency": round(consistent / total_pw, 3) if total_pw > 0 else None,
            "pairwise_winner": name_a if wins_a > wins_b else (name_b if wins_b > wins_a else "tie"),
        }

    # ── Best / Worst cases (for the report) ──
    if any(e.get("pointwise") for e in evaluations if not e.get("skipped")):
        case_deltas = []
        for e in evaluations:
            if e.get("skipped") or not e.get("pointwise"):
                continue
            # Compute mean score delta across all dimensions
            deltas = []
            for dim in dimensions:
                sa = e["pointwise"].get(key_a, {}).get(dim, {}).get("score")
                sb = e["pointwise"].get(key_b, {}).get(dim, {}).get("score")
                if sa is not None and sb is not None:
                    deltas.append(sa - sb)
            if deltas:
                case_deltas.append({
                    "test_case_id": e["test_case_id"],
                    "category": e["category"],
                    "input": e["input"],
                    "mean_delta": round(float(np.mean(deltas)), 3),  # positive = A better
                })

        case_deltas.sort(key=lambda x: x["mean_delta"])

        analysis["notable_cases"] = {
            f"best_for_{name_b}": case_deltas[:3] if case_deltas else [],  # most negative delta = B much better
            f"best_for_{name_a}": case_deltas[-3:][::-1] if case_deltas else [],  # most positive delta = A much better
        }

    # ── Generate recommendation ──
    analysis["recommendation"] = generate_recommendation(analysis, name_a, name_b)

    # ── Operational metrics ──
    run_data = _load_run_data(eval_data, run_path, output_dir)
    if run_data is not None:
        analysis["operational_metrics"] = compute_operational_metrics(run_data)

    # Save
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    base_id = eval_data["eval_id"].removeprefix("eval_")
    analysis_id = f"analysis_{base_id}"
    analysis_file = output_path / f"analysis_{base_id}.json"

    output = {
        "analysis_id": analysis_id,
        "eval_id": eval_data["eval_id"],
        "run_id": eval_data["run_id"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "analysis": analysis,
    }

    with open(analysis_file, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Analysis saved to {analysis_file}")
    return str(analysis_file)


def generate_recommendation(analysis: dict, name_a: str, name_b: str) -> dict:
    """
    Generate a structured recommendation based on all available data.
    """
    signals = {"for_a": 0, "for_b": 0, "confidence": "low"}

    # Signal 1: pointwise overall
    pw = analysis.get("pointwise", {}).get("overall_weighted", {})
    if pw:
        if pw.get("better") == name_a:
            signals["for_a"] += 1
        else:
            signals["for_b"] += 1

    # Signal 2: pairwise win rate
    pair = analysis.get("pairwise", {})
    pw_winner = pair.get("pairwise_winner")
    if pw_winner == name_a:
        signals["for_a"] += 1
    elif pw_winner == name_b:
        signals["for_b"] += 1

    # Signal 3: statistical significance
    dims = analysis.get("pointwise", {}).get("dimensions", {})
    sig_for_a = sum(
        1 for d in dims.values()
        if d["comparison"]["ttest"].get("significant_005")
        and d["comparison"]["better"] == name_a
    )
    sig_for_b = sum(
        1 for d in dims.values()
        if d["comparison"]["ttest"].get("significant_005")
        and d["comparison"]["better"] == name_b
    )
    if sig_for_a > sig_for_b:
        signals["for_a"] += 1
    elif sig_for_b > sig_for_a:
        signals["for_b"] += 1

    # Determine confidence
    total_signals = signals["for_a"] + signals["for_b"]
    if total_signals >= 2 and abs(signals["for_a"] - signals["for_b"]) >= 2:
        signals["confidence"] = "high"
    elif total_signals >= 1:
        signals["confidence"] = "medium"

    # Winner
    if signals["for_a"] > signals["for_b"]:
        winner = name_a
    elif signals["for_b"] > signals["for_a"]:
        winner = name_b
    else:
        winner = "inconclusive"

    return {
        "winner": winner,
        "confidence": signals["confidence"],
        "signals": signals,
    }
