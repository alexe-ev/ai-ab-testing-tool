"""
Reporter: generates human-readable and machine-readable reports.

Pipeline: analysis_XXX.json + run_XXX.json → Reporter → report.md + summary.json

Markdown report includes: summary table, dimension breakdown,
category analysis, notable cases, and recommendation.
"""

import json
from pathlib import Path
from datetime import datetime, timezone


def load_json(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


# ─── Markdown report generation ───────────────────────────────────

def generate_markdown_report(
    analysis_path: str,
    run_path: str,
    output_dir: str = "results",
) -> str:
    """
    Generate a comprehensive markdown report from analysis + run data.
    Returns path to the markdown file.
    """
    analysis_data = load_json(analysis_path)
    run_data = load_json(run_path)

    a = analysis_data["analysis"]
    name_a = a["prompt_a"]["name"]
    name_b = a["prompt_b"]["name"]

    lines = []

    # ── Header ──
    exp_name = run_data["config"]["experiment"].get("name", "Unnamed")
    lines.append(f"# A/B Test Report: {exp_name}")
    lines.append("")
    lines.append(f"**Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append(f"**Model:** {run_data['config']['model']['name']}")
    lines.append(f"**Test cases:** {run_data['summary']['total_cases']}")
    lines.append(f"**Prompts:** {name_a} vs {name_b}")
    lines.append("")

    # ── Recommendation (upfront) ──
    rec = a.get("recommendation", {})
    winner = rec.get("winner", "inconclusive")
    confidence = rec.get("confidence", "low")

    lines.append("## Recommendation")
    lines.append("")
    if winner == "inconclusive":
        lines.append(f"**Result: Inconclusive.** The data does not clearly favor either prompt. Consider adding more test cases or refining the rubric.")
    else:
        emoji = "🟢" if confidence == "high" else "🟡"
        lines.append(f"**{emoji} Recommended: {winner}** (confidence: {confidence})")
    lines.append("")

    # ── Pointwise scores table ──
    pw = a.get("pointwise", {})
    dims = pw.get("dimensions", {})

    if dims:
        lines.append("## Scores by Dimension")
        lines.append("")
        lines.append(f"| Dimension | {name_a} | {name_b} | Δ | p-value | Effect | Winner |")
        lines.append("|-----------|---------|---------|---|---------|--------|--------|")

        for dim_name, dim_data in dims.items():
            mean_a = dim_data[name_a]["mean"]
            mean_b = dim_data[name_b]["mean"]
            std_a = dim_data[name_a]["std"]
            std_b = dim_data[name_b]["std"]
            diff = dim_data["comparison"]["mean_diff"]
            p_val = dim_data["comparison"]["ttest"].get("p_value")
            d_val = dim_data["comparison"].get("cohens_d")
            effect = dim_data["comparison"].get("effect_interpretation", "?")
            better = dim_data["comparison"]["better"]

            p_str = f"{p_val:.3f}" if p_val is not None else "n/a"
            d_str = f"{d_val:.2f}" if d_val is not None else "n/a"

            # Star for significance
            sig_marker = ""
            if p_val is not None and p_val < 0.05:
                sig_marker = " ★"
            elif p_val is not None and p_val < 0.10:
                sig_marker = " ☆"

            lines.append(
                f"| {dim_name} | {mean_a:.2f} ± {std_a:.2f} | {mean_b:.2f} ± {std_b:.2f} "
                f"| {diff:+.2f} | {p_str}{sig_marker} | {d_str} ({effect}) | {better} |"
            )

        # Overall
        overall = pw.get("overall_weighted", {})
        if overall:
            lines.append(f"| **Overall (weighted)** | **{overall.get(name_a, 0):.2f}** | **{overall.get(name_b, 0):.2f}** "
                         f"| | | | **{overall.get('better', '?')}** |")

        lines.append("")
        lines.append("★ = significant at p < 0.05, ☆ = significant at p < 0.10")
        lines.append("")

    # ── Pairwise results ──
    pair = a.get("pairwise", {})
    if pair:
        lines.append("## Head-to-Head Comparison")
        lines.append("")
        total = pair.get("total", 0)
        wins_a = pair.get(f"wins_{name_a}", 0)
        wins_b = pair.get(f"wins_{name_b}", 0)
        ties = pair.get("ties", 0)
        uncertain = pair.get("uncertain", 0)
        consistency = pair.get("swap_test_consistency")
        wr_a = pair.get(f"win_rate_{name_a}")
        wr_b = pair.get(f"win_rate_{name_b}")

        lines.append(f"Out of {total} comparisons:")
        lines.append(f"- **{name_a}** wins: {wins_a} ({wr_a*100:.0f}%)" if wr_a else f"- **{name_a}** wins: {wins_a}")
        lines.append(f"- **{name_b}** wins: {wins_b} ({wr_b*100:.0f}%)" if wr_b else f"- **{name_b}** wins: {wins_b}")
        lines.append(f"- Ties: {ties}")
        if uncertain > 0:
            lines.append(f"- Uncertain (positional bias detected): {uncertain}")
        if consistency is not None:
            pct = consistency * 100
            status = "✅ reliable" if pct >= 80 else "⚠️ some positional bias"
            lines.append(f"\nSwap test consistency: {pct:.0f}% ({status})")
        lines.append("")

    # ── Category breakdown ──
    cats = a.get("category_breakdown", {})
    if cats:
        lines.append("## Breakdown by Category")
        lines.append("")
        lines.append(f"| Category | N | {name_a} | {name_b} | Better |")
        lines.append("|----------|---|---------|---------|--------|")
        for cat, data in sorted(cats.items()):
            lines.append(
                f"| {cat} | {data['n_cases']} | {data[name_a]:.2f} | {data[name_b]:.2f} | {data['better']} |"
            )
        lines.append("")

    # ── Notable cases ──
    notable = a.get("notable_cases", {})
    for label, cases in notable.items():
        if cases:
            pretty_label = label.replace("best_for_", "Best cases for ")
            lines.append(f"## {pretty_label}")
            lines.append("")
            for c in cases:
                lines.append(f"**{c['test_case_id']}** ({c['category']}, Δ = {c['mean_delta']:+.2f})")
                # Truncate long inputs
                input_text = c["input"][:200] + "..." if len(c["input"]) > 200 else c["input"]
                lines.append(f"> {input_text}")
                lines.append("")

    # ── Methodology note ──
    lines.append("---")
    lines.append("")
    lines.append("## Methodology")
    lines.append("")
    lines.append("This report was generated by **prompt-ab**, a framework for data-driven prompt selection.")
    lines.append("")
    lines.append("**Evaluation approach:** Each response was scored independently (pointwise, 1-5 scale) by an LLM judge, "
                 "and each pair was compared head-to-head (pairwise) with a swap test to detect positional bias.")
    lines.append("")
    lines.append("**Statistical tests:** Paired t-test for significance, Cohen's d for effect size, "
                 "bootstrap (10,000 samples) for 95% confidence intervals.")
    lines.append("")

    # Write file
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    base_id = analysis_data["analysis_id"].removeprefix("analysis_")
    report_file = output_path / f"report_{base_id}.md"

    with open(report_file, "w") as f:
        f.write("\n".join(lines))

    print(f"✅ Markdown report saved to {report_file}")
    return str(report_file)


# ─── Summary JSON (for CI/CD) ─────────────────────────────────────

def generate_summary_json(analysis_path: str, output_dir: str = "results") -> str:
    """
    Compact JSON summary for automated pipelines (CI/CD gates).
    Returns path to summary JSON file.
    """
    analysis_data = load_json(analysis_path)
    a = analysis_data["analysis"]
    name_a = a["prompt_a"]["name"]
    name_b = a["prompt_b"]["name"]

    # Extract key metrics
    pw = a.get("pointwise", {})
    overall = pw.get("overall_weighted", {})

    dims_summary = {}
    for dim_name, dim_data in pw.get("dimensions", {}).items():
        dims_summary[dim_name] = {
            "score_a": dim_data[name_a]["mean"],
            "score_b": dim_data[name_b]["mean"],
            "p_value": dim_data["comparison"]["ttest"].get("p_value"),
            "effect_size": dim_data["comparison"].get("cohens_d"),
        }

    pair = a.get("pairwise", {})
    rec = a.get("recommendation", {})

    summary = {
        "run_id": analysis_data["run_id"],
        "prompt_a": name_a,
        "prompt_b": name_b,
        "recommendation": rec.get("winner", "inconclusive"),
        "confidence": rec.get("confidence", "low"),
        "overall_score_a": overall.get(name_a),
        "overall_score_b": overall.get(name_b),
        "win_rate_a": pair.get(f"win_rate_{name_a}"),
        "win_rate_b": pair.get(f"win_rate_{name_b}"),
        "swap_consistency": pair.get("swap_test_consistency"),
        "dimensions": dims_summary,
    }

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    base_id = analysis_data["analysis_id"].removeprefix("analysis_")
    summary_file = output_path / f"summary_{base_id}.json"

    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"✅ Summary JSON saved to {summary_file}")
    return str(summary_file)
