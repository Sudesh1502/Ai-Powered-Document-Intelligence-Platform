"""
This file handles metadata extraction from text using Azure OpenAI.
"""
import json

from openai import AzureOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log
import logging

# Configure a basic logger for tenacity
logger = logging.getLogger("tenacity.retry")
logger.setLevel(logging.WARNING)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("[SYSTEM_WARNING] %(message)s"))
    logger.addHandler(ch)

from src.config.config import AZURE_OPENAI_DEPLOYMENT_NAME
from src.utils.llm_client import get_llm_client
from src.utils.get_prompt import get_metadata_extraction_prompt
from src.utils.llm_cost_calculator import calculate_llm_cost


@retry(
    stop=stop_after_attempt(5), 
    wait=wait_exponential(multiplier=1, min=2, max=10),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
def _generate_content_with_retry(prompt: str):
    """Helper function to call Azure OpenAI with automatic retries on failure."""
    client = get_llm_client()
    return client.chat.completions.create(
        model=AZURE_OPENAI_DEPLOYMENT_NAME,
        messages=[{"role": "user", "content": prompt}],
    )


def _log_usage(response, label: str = "LLM"):
    """Logs token usage and estimated cost from the API response."""
    try:
        usage = response.usage
        print(f"\n===== {label} USAGE =====")
        print("Prompt Tokens  :", usage.prompt_tokens)
        print("Output Tokens  :", usage.completion_tokens)
        print("Total Tokens   :", usage.total_tokens)
        calculate_llm_cost(
            prompt_tokens=usage.prompt_tokens,
            output_tokens=usage.completion_tokens,
        )
        print("========================\n")
    except Exception as e:
        print("Usage metadata unavailable:", e)


def _parse_json_response(response) -> dict | list:
    """Strips markdown fences and parses JSON from the LLM response."""
    content = response.choices[0].message.content
    if not content:
        return {}
    output = content.strip()
    if "```json" in output:
        output = output.replace("```json", "")
    if "```" in output:
        output = output.replace("```", "")
    return json.loads(output.strip())


def extract_metadata(text, user_id="default_global"):
    """Extracts structured metadata (JSON) from raw text using Azure OpenAI."""
    print("\nExtracting metadata...")

    prompt = get_metadata_extraction_prompt(text, user_id)

    try:
        client = get_llm_client()
        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=[{"role": "user", "content": prompt}],
        )

        _log_usage(response, "METADATA")

        if not response.choices[0].message.content:
            return {"error": "Empty response from Azure OpenAI"}

        metadata = _parse_json_response(response)

        # Safety net: If model hallucinates and returns a list, unwrap it
        if isinstance(metadata, list) and len(metadata) > 0:
            metadata = metadata[0]

        print("\nMetadata extraction completed...")
        return metadata

    except Exception as e:
        print(f"Azure OpenAI Error: {e}")
        return {}


def extract_policy_metadata(text, user_id="default_global"):
    """Extracts structured policy metadata (JSON) for the Master Index using Azure OpenAI."""
    print("\nExtracting policy metadata...")

    from src.utils.get_prompt import get_policy_extraction_prompt
    prompt = get_policy_extraction_prompt(text, user_id)

    try:
        response = _generate_content_with_retry(prompt)

        _log_usage(response, "POLICY")

        if not response.choices[0].message.content:
            return {"error": "Empty response from Azure OpenAI"}

        metadata = _parse_json_response(response)

        # Safety net: If model returns a single dict instead of a list, wrap it
        if isinstance(metadata, dict):
            metadata = [metadata]

        print("\nPolicy Metadata extraction completed...")
        return metadata

    except Exception as e:
        print(f"Azure OpenAI Policy Error: {e}")
        return {}
