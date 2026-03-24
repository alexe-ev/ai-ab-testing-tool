"""
Pricing table for LLM models.

Used to estimate cost per run based on token counts.
Prices are in USD per 1 million tokens.
"""

# Model prefix -> {input_price_per_1m, output_price_per_1m}
PRICING_TABLE: dict[str, dict[str, float]] = {
    "gpt-4o-mini": {"input_price_per_1m": 0.15, "output_price_per_1m": 0.60},
    "gpt-4o": {"input_price_per_1m": 2.50, "output_price_per_1m": 10.00},
    "gpt-4.1-mini": {"input_price_per_1m": 0.40, "output_price_per_1m": 1.60},
    "gpt-4.1": {"input_price_per_1m": 2.00, "output_price_per_1m": 8.00},
    "claude-haiku": {"input_price_per_1m": 0.80, "output_price_per_1m": 4.00},
    "claude-sonnet": {"input_price_per_1m": 3.00, "output_price_per_1m": 15.00},
    "claude-opus": {"input_price_per_1m": 15.00, "output_price_per_1m": 75.00},
}


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float | None:
    """
    Estimate cost in USD for a given model and token counts.

    Matches by prefix (longest match first) so that e.g.
    'gpt-4o-mini' takes priority over 'gpt-4o'.

    Returns None if the model is not in the pricing table.
    """
    matched_prefix = None
    for prefix in sorted(PRICING_TABLE.keys(), key=len, reverse=True):
        if model.startswith(prefix):
            matched_prefix = prefix
            break

    if matched_prefix is None:
        return None

    prices = PRICING_TABLE[matched_prefix]
    cost = (
        input_tokens * prices["input_price_per_1m"] / 1_000_000
        + output_tokens * prices["output_price_per_1m"] / 1_000_000
    )
    return round(cost, 6)
