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


def run_experiment(config_path: str, output_dir: str = "results", dry_run: bool = False, on_progress=None) -> str:
    """
    Main runner: loads config, iterates test cases, calls LLM for each prompt.

    Returns path to the results JSON file.
    """
    config = load_config(config_path)
    test_cases = load_test_set(config["test_set"])
    run_id = generate_run_id(config)

    model_cfg = config["model"]
    default_model = model_cfg["name"]
    temperature = model_cfg.get("temperature", 0.3)
    max_tokens = model_cfg.get("max_tokens", 1024)

    prompts = config["prompts"]
    prompt_names = list(prompts.keys())

    # Resolve per-prompt models and providers
    prompt_models = {}
    for key, pcfg in prompts.items():
        m = pcfg.get("model", default_model)
        p = detect_provider(m, model_cfg.get("provider") if m == default_model else None)
        prompt_models[key] = {"model": m, "provider": p}

    # Check if all prompts use the same model
    unique_models = set(pm["model"] for pm in prompt_models.values())
    single_model = len(unique_models) == 1

    print(f"\n{'━' * 50}")
    print(f"  Experiment: {config['experiment'].get('name', 'unnamed')}")
    if single_model:
        m = next(iter(prompt_models.values()))
        print(f"  Model: {m['model']} ({m['provider']})")
    else:
        for key in prompt_names:
            pm = prompt_models[key]
            label = prompts[key].get("name", key)
            print(f"  {label}: {pm['model']} ({pm['provider']})")
    print(f"  Prompts: {', '.join(prompt_names)}")
    print(f"  Test cases: {len(test_cases)}")
    print(f"  Total API calls: {len(test_cases) * len(prompt_names)}")
    print(f"{'━' * 50}\n")

    if dry_run:
        print("🏁 Dry run complete. No API calls made.")
        return ""

    # Create one client per unique provider
    clients = {}
    for pm in prompt_models.values():
        if pm["provider"] not in clients:
            clients[pm["provider"]] = create_client(pm["provider"])

    results = []
    total_calls = len(test_cases) * len(prompt_names)
    call_num = 0

    for i, case in enumerate(test_cases):
        context = case.get("context")

        # Compose user input: prepend context if present
        if context:
            user_input = (
                f"[Retrieved context]\n{context}\n\n"
                f"[User question]\n{case['input']}"
            )
        else:
            user_input = case["input"]

        case_results = {
            "test_case_id": case["id"],
            "category": case.get("category", "unknown"),
            "input": case["input"],
            "context": context,
            "reference": case.get("reference"),
            "responses": {},
        }

        for prompt_key in prompt_names:
            call_num += 1
            prompt_cfg = prompts[prompt_key]
            system = prompt_cfg["system"]
            pm = prompt_models[prompt_key]

            label = prompt_cfg.get('name', prompt_key)
            print(f"  [{call_num}/{total_calls}] {case['id']} × {label}...", end=" ", flush=True)

            if on_progress:
                on_progress({
                    "step": "running",
                    "case_id": case["id"],
                    "case_index": i + 1,
                    "total": len(test_cases),
                    "detail": f"Calling {pm['model']} for {label}: {case['id']}",
                    "type": "info",
                })

            result = call_llm(
                client=clients[pm["provider"]],
                system_prompt=system,
                user_input=user_input,
                model=pm["model"],
                provider=pm["provider"],
                temperature=temperature,
                max_tokens=max_tokens,
            )

            case_results["responses"][prompt_key] = result

            if result.get("error"):
                print(f"❌ {result['error']}")
                if on_progress:
                    on_progress({
                        "step": "running",
                        "case_id": case["id"],
                        "case_index": i + 1,
                        "total": len(test_cases),
                        "detail": f"Error: {result['error']}",
                        "type": "error",
                    })
            else:
                tokens = result["input_tokens"] + result["output_tokens"]
                print(f"✓ ({tokens} tokens, {result['latency_seconds']}s)")
                if on_progress:
                    on_progress({
                        "step": "running",
                        "case_id": case["id"],
                        "case_index": i + 1,
                        "total": len(test_cases),
                        "detail": f"{label}: {tokens} tokens, {result['latency_seconds']}s",
                        "type": "success",
                    })

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
            "prompt_models": {k: pm["model"] for k, pm in prompt_models.items()},
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
