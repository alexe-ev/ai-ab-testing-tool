"""
Runner: executes both prompts against every test case via LLM API.

Pipeline: config.yaml + test_set.yaml → Runner → results/run_XXX.json

Each test case produces two API calls (one per prompt). All responses,
tokens, costs, and latencies are saved for downstream evaluation.
"""

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import yaml

from src.llm import detect_provider, create_client, call_llm


def load_config(config_path: str) -> dict:
    """Load and validate experiment configuration."""
    with open(config_path) as f:
        config = yaml.safe_load(f)

    required = ["experiment", "model", "prompts", "test_set", "rubric"]
    missing = [k for k in required if k not in config]
    if missing:
        raise ValueError(f"Config missing required keys: {missing}")

    if len(config["prompts"]) < 2:
        raise ValueError("Need at least 2 prompts to compare")

    return config


def load_test_set(path: str) -> list[dict]:
    """Load test cases from YAML file."""
    with open(path) as f:
        data = yaml.safe_load(f)
    cases = data.get("test_cases", [])
    if not cases:
        raise ValueError(f"No test_cases found in {path}")
    return cases


def generate_run_id(config: dict) -> str:
    """Deterministic run ID from experiment name + timestamp."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    name = config["experiment"].get("name", "experiment")
    h = hashlib.md5(f"{name}_{ts}".encode()).hexdigest()[:6]
    return f"{name}_{ts}_{h}"


def run_experiment(config_path: str, output_dir: str = "results", dry_run: bool = False) -> str:
    """
    Main runner: loads config, iterates test cases, calls LLM for each prompt.

    Returns path to the results JSON file.
    """
    config = load_config(config_path)
    test_cases = load_test_set(config["test_set"])
    run_id = generate_run_id(config)

    model_cfg = config["model"]
    model = model_cfg["name"]
    temperature = model_cfg.get("temperature", 0.3)
    max_tokens = model_cfg.get("max_tokens", 1024)
    provider = detect_provider(model, model_cfg.get("provider"))

    prompts = config["prompts"]
    prompt_names = list(prompts.keys())

    print(f"\n{'━' * 50}")
    print(f"  Experiment: {config['experiment'].get('name', 'unnamed')}")
    print(f"  Model: {model} ({provider})")
    print(f"  Prompts: {', '.join(prompt_names)}")
    print(f"  Test cases: {len(test_cases)}")
    print(f"  Total API calls: {len(test_cases) * len(prompt_names)}")
    print(f"{'━' * 50}\n")

    if dry_run:
        print("🏁 Dry run complete. No API calls made.")
        return ""

    client = create_client(provider)
    results = []
    total_calls = len(test_cases) * len(prompt_names)
    call_num = 0

    for i, case in enumerate(test_cases):
        case_results = {
            "test_case_id": case["id"],
            "category": case.get("category", "unknown"),
            "input": case["input"],
            "reference": case.get("reference"),
            "responses": {},
        }

        for prompt_key in prompt_names:
            call_num += 1
            prompt_cfg = prompts[prompt_key]
            system = prompt_cfg["system"]

            print(f"  [{call_num}/{total_calls}] {case['id']} × {prompt_cfg.get('name', prompt_key)}...", end=" ", flush=True)

            result = call_llm(
                client=client,
                system_prompt=system,
                user_input=case["input"],
                model=model,
                provider=provider,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            case_results["responses"][prompt_key] = result

            if result.get("error"):
                print(f"❌ {result['error']}")
            else:
                tokens = result["input_tokens"] + result["output_tokens"]
                print(f"✓ ({tokens} tokens, {result['latency_seconds']}s)")

        results.append(case_results)

    # Save results
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    results_file = output_path / f"run_{run_id}.json"

    output = {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config": {
            "experiment": config["experiment"],
            "model": model_cfg,
            "prompt_names": {k: v.get("name", k) for k, v in prompts.items()},
        },
        "results": results,
        "summary": {
            "total_cases": len(test_cases),
            "total_calls": call_num,
            "errors": sum(
                1 for r in results
                for resp in r["responses"].values()
                if resp.get("error")
            ),
        },
    }

    with open(results_file, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Results saved to {results_file}")
    print(f"   {output['summary']['total_cases']} cases, {output['summary']['errors']} errors")

    return str(results_file)
