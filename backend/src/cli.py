"""
CLI: command-line interface for the prompt A/B testing framework.

Usage:
  prompt-ab run --config experiment.yaml          # Full pipeline
  prompt-ab run --config experiment.yaml --dry-run # Preview without API calls
  prompt-ab evaluate --results run.json --rubric rubric.yaml
  prompt-ab analyze --eval eval.json
  prompt-ab report --analysis analysis.json --run run.json

Each subcommand can be run independently (useful when iterating on
rubrics or re-generating reports without re-running API calls).
"""

import os
import click
from pathlib import Path

from src.runner import run_experiment, load_config
from src.evaluator import evaluate_run
from src.analyzer import analyze_evaluation
from src.reporter import generate_markdown_report, generate_summary_json
from src.html_report import generate_html_report


def require_api_key(config):
    """Check that the right API keys are set for all configured providers."""
    from src.llm import detect_provider, get_env_key

    providers_needed = set()

    # Global model
    model_cfg = config.get("model", {})
    providers_needed.add(
        detect_provider(model_cfg.get("name", ""), model_cfg.get("provider"))
    )

    # Per-prompt model overrides
    for prompt_cfg in config.get("prompts", {}).values():
        if "model" in prompt_cfg:
            providers_needed.add(detect_provider(prompt_cfg["model"]))

    missing = []
    for provider in providers_needed:
        key_name = get_env_key(provider)
        if not os.environ.get(key_name):
            missing.append(key_name)

    if missing:
        raise click.ClickException(
            "API keys not set:\n" +
            "\n".join(f"  export {k}=..." for k in sorted(missing))
        )


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """prompt-ab: data-driven A/B testing for LLM prompts."""
    pass


@cli.command()
@click.option("--config", "-c", required=True, help="Path to experiment YAML config")
@click.option("--output", "-o", default="results", help="Output directory")
@click.option("--dry-run", is_flag=True, help="Preview experiment without API calls")
@click.option("--eval-only", is_flag=True, help="Skip LLM run, just evaluate + analyze + report")
@click.option("--judge-model", default="claude-sonnet-4-20250514", help="Model for LLM-as-judge")
@click.option("--eval-mode", default="both", type=click.Choice(["pointwise", "pairwise", "both"]))
def run(config, output, dry_run, eval_only, judge_model, eval_mode):
    """Run the full A/B testing pipeline: execute → evaluate → analyze → report."""

    cfg = load_config(config)

    if dry_run:
        run_experiment(config, output, dry_run=True)
        return

    require_api_key(cfg)

    # Step 1: Run prompts through LLM API
    if not eval_only:
        click.echo("\n📋 Step 1/4: Running prompts through LLM...")
        results_path = run_experiment(config, output)
        if not results_path:
            click.echo("❌ Run failed.")
            return
    else:
        # Find most recent run file
        results_files = sorted(Path(output).glob("run_*.json"), reverse=True)
        if not results_files:
            click.echo(f"❌ No run files found in {output}/. Run without --eval-only first.")
            return
        results_path = str(results_files[0])
        click.echo(f"\n📋 Using existing run: {results_path}")

    # Step 2: Evaluate with LLM-as-judge
    click.echo("\n⚖️  Step 2/4: Evaluating with LLM-as-judge...")
    rubric_path = cfg["rubric"]
    eval_path = evaluate_run(results_path, rubric_path, output, eval_mode, judge_model)

    # Step 3: Statistical analysis
    click.echo("\n📊 Step 3/4: Statistical analysis...")
    analysis_path = analyze_evaluation(eval_path, output)

    # Step 4: Generate reports
    click.echo("\n📝 Step 4/4: Generating reports...")
    report_path = generate_markdown_report(analysis_path, results_path, output)
    summary_path = generate_summary_json(analysis_path, output)
    html_path = generate_html_report(analysis_path, results_path, eval_path, output)

    # Final summary
    click.echo(f"\n{'━' * 50}")
    click.echo("  ✅ Pipeline complete!")
    click.echo(f"  📄 Report:  {report_path}")
    click.echo(f"  🌐 HTML:    {html_path}")
    click.echo(f"  📊 Summary: {summary_path}")
    click.echo(f"  📁 All files in: {output}/")
    click.echo(f"{'━' * 50}\n")


@cli.command()
@click.option("--results", "-r", required=True, help="Path to run results JSON")
@click.option("--rubric", required=True, help="Path to rubric YAML")
@click.option("--output", "-o", default="results", help="Output directory")
@click.option("--mode", default="both", type=click.Choice(["pointwise", "pairwise", "both"]))
@click.option("--judge-model", default="claude-sonnet-4-20250514")
def evaluate(results, rubric, output, mode, judge_model):
    """Evaluate run results with LLM-as-judge (without re-running prompts)."""
    require_api_key({"model": {"name": judge_model}})
    eval_path = evaluate_run(results, rubric, output, mode, judge_model)
    click.echo(f"\n✅ Evaluation complete: {eval_path}")


@cli.command()
@click.option("--eval", "eval_path", required=True, help="Path to evaluation JSON")
@click.option("--output", "-o", default="results")
def analyze(eval_path, output):
    """Run statistical analysis on evaluation results."""
    analysis_path = analyze_evaluation(eval_path, output)
    click.echo(f"\n✅ Analysis complete: {analysis_path}")


@cli.command()
@click.option("--analysis", "-a", required=True, help="Path to analysis JSON")
@click.option("--run", "run_path", required=True, help="Path to original run JSON")
@click.option("--eval", "eval_path", required=True, help="Path to evaluation JSON")
@click.option("--output", "-o", default="results")
def report(analysis, run_path, eval_path, output):
    """Generate markdown report, HTML dashboard, and summary JSON."""
    report_path = generate_markdown_report(analysis, run_path, output)
    summary_path = generate_summary_json(analysis, output)
    html_path = generate_html_report(analysis, run_path, eval_path, output)
    click.echo(f"\n✅ Report: {report_path}")
    click.echo(f"✅ HTML:   {html_path}")
    click.echo(f"✅ Summary: {summary_path}")


if __name__ == "__main__":
    cli()
