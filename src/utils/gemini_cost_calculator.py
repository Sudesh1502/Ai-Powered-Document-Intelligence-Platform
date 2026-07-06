def calculate_gemini_cost(
    prompt_tokens,
    output_tokens,
    input_cost_per_million,
    output_cost_per_million
):

    input_cost = (
        prompt_tokens / 1_000_000
    ) * input_cost_per_million

    output_cost = (
        output_tokens / 1_000_000
    ) * output_cost_per_million

    total_cost = (
        input_cost +
        output_cost
    )

    print("\n===== GEMINI COST =====")

    print(f"Prompt Tokens : {prompt_tokens:,}")
    print(f"Output Tokens : {output_tokens:,}")
    print(f"Total Tokens  : {prompt_tokens + output_tokens:,}")

    print()

    print(f"Input Cost    : ${input_cost:.8f}")
    print(f"Output Cost   : ${output_cost:.8f}")
    print(f"Total Cost    : ${total_cost:.8f}")

    print("=======================\n")

    return total_cost