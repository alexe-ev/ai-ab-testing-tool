"""
LLM client abstraction. Supports Anthropic and OpenAI APIs.

Provider is determined by model config: provider field or auto-detected from model name.
"""

import os
import time
from pathlib import Path


def load_dotenv():
    """Load .env file from project root if it exists."""
    env_file = Path(__file__).parent.parent / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value


load_dotenv()


def detect_provider(model: str, explicit: str | None = None) -> str:
    """Detect provider from explicit config or model name."""
    if explicit:
        return explicit.lower()
    if model.startswith(("claude-", "claude3")):
        return "anthropic"
    if model.startswith(("gpt-", "o1", "o3", "o4")):
        return "openai"
    return "openai"


def get_env_key(provider: str) -> str:
    if provider == "anthropic":
        return "ANTHROPIC_API_KEY"
    return "OPENAI_API_KEY"


def check_api_key(provider: str):
    key_name = get_env_key(provider)
    if not os.environ.get(key_name):
        raise RuntimeError(
            f"{key_name} not set. Export it before running:\n"
            f"  export {key_name}=..."
        )


def create_client(provider: str):
    check_api_key(provider)
    if provider == "anthropic":
        import anthropic
        return anthropic.Anthropic()
    else:
        import openai
        return openai.OpenAI()


def call_llm(
    client,
    system_prompt: str,
    user_input: str,
    model: str,
    provider: str,
    temperature: float = 0.3,
    max_tokens: int = 1024,
) -> dict:
    """
    Single LLM API call. Returns response text + metadata.
    Retries up to 3 times on transient errors.
    """
    if provider == "anthropic":
        return _call_anthropic(client, system_prompt, user_input, model, temperature, max_tokens)
    else:
        return _call_openai(client, system_prompt, user_input, model, temperature, max_tokens)


def _call_anthropic(client, system_prompt, user_input, model, temperature, max_tokens) -> dict:
    import anthropic

    for attempt in range(3):
        try:
            start = time.time()
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_input}],
            )
            latency = time.time() - start

            return {
                "response": response.content[0].text,
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "latency_seconds": round(latency, 3),
                "model": model,
                "stop_reason": response.stop_reason,
            }

        except anthropic.RateLimitError:
            wait = 2 ** attempt * 5
            print(f"  ⏳ Rate limited, waiting {wait}s...")
            time.sleep(wait)

        except anthropic.APIError as e:
            if attempt == 2:
                return {"error": str(e), "response": None}
            time.sleep(2 ** attempt)

    return {"error": "Max retries exceeded", "response": None}


def _call_openai(client, system_prompt, user_input, model, temperature, max_tokens) -> dict:
    import openai

    for attempt in range(3):
        try:
            start = time.time()
            response = client.chat.completions.create(
                model=model,
                max_completion_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input},
                ],
            )
            latency = time.time() - start

            choice = response.choices[0]
            usage = response.usage

            return {
                "response": choice.message.content,
                "input_tokens": usage.prompt_tokens,
                "output_tokens": usage.completion_tokens,
                "latency_seconds": round(latency, 3),
                "model": model,
                "stop_reason": choice.finish_reason,
            }

        except openai.RateLimitError:
            wait = 2 ** attempt * 5
            print(f"  ⏳ Rate limited, waiting {wait}s...")
            time.sleep(wait)

        except openai.APIError as e:
            if attempt == 2:
                return {"error": str(e), "response": None}
            time.sleep(2 ** attempt)

    return {"error": "Max retries exceeded", "response": None}
