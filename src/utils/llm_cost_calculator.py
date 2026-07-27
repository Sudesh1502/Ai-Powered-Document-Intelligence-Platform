"""
Generic LLM cost calculator for Azure OpenAI.
Default pricing is set for GPT-4o mini (as of 2025).
Adjust input_cost_per_million / output_cost_per_million per your deployment.
"""

# GPT-4o mini pricing (per 1M tokens)
# Input : $0.15 / 1M tokens
# Output: $0.60 / 1M tokens


def calculate_llm_cost(
    prompt_tokens: int,
    output_tokens: int,
    input_cost_per_million: float = 0.15,   # GPT-4o mini default
    output_cost_per_million: float = 0.60,  # GPT-4o mini default
) -> float:

    input_cost  = (prompt_tokens  / 1_000_000) * input_cost_per_million
    output_cost = (output_tokens  / 1_000_000) * output_cost_per_million
    total_cost  = input_cost + output_cost

    print("\n===== AZURE OPENAI COST =====")
    print(f"Prompt Tokens : {prompt_tokens:,}")
    print(f"Output Tokens : {output_tokens:,}")
    print(f"Total Tokens  : {prompt_tokens + output_tokens:,}")
    print()
    print(f"Input Cost    : ${input_cost:.8f}")
    print(f"Output Cost   : ${output_cost:.8f}")
    print(f"Total Cost    : ${total_cost:.8f}")
    print("=============================\n")

    return total_cost
