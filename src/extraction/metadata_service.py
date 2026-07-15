"""
This file handles metadata extraction from text using a Generative AI model.
"""
import json

from google import genai

from src.config.config import GEMINI_API_KEY
from src.utils.get_prompt import get_metadata_extraction_prompt
from tenacity import retry, stop_after_attempt, wait_exponential
from src.utils.gemini_cost_calculator import calculate_gemini_cost


client = genai.Client(
    api_key=GEMINI_API_KEY
)

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=10))
def _generate_content_with_retry(prompt):
    """Helper function to call Gemini API with automatic retries on failure."""
    return client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt
    )


def extract_metadata(text, user_id="default_global"):
    """Extracts structured metadata (JSON) from raw text using Gemini."""
    print("\nExtracting metadata...")

    prompt = get_metadata_extraction_prompt(text, user_id)

    try:

        #we are trying to retry the meta data extraction whenever server is busy of gemini.
        response = client.models.generate_content(
                   model="gemini-3.1-flash-lite",
                   contents=prompt
                 )
        
        print("\n===== GEMINI USAGE =====")

        try:

            usage = response.usage_metadata

            print(usage)

            print(
                "Prompt Tokens:",
                usage.prompt_token_count
            )

            print(
                "Output Tokens:",
                usage.candidates_token_count
            )

            print(
                "Total Tokens:",
                usage.total_token_count
            )
            calculate_gemini_cost(
            prompt_tokens=usage.prompt_token_count,
            output_tokens=usage.candidates_token_count,
            input_cost_per_million=0.25,   # set accordingly
            output_cost_per_million=1.50   # set accordingly as per latest pricing
        )

        except Exception as e:

            print(
                "Usage metadata unavailable:",
                e
            )

        print("========================\n")   

        if not response.text:
            return {
                "error": "Empty response from Gemini"
            }

        output = response.text.strip()

        if "```json" in output:
            output = output.replace("```json", "")

        if "```" in output:
            output = output.replace("```", "")

        output = output.strip()

        metadata = json.loads(output)
        
        # Safety net: If Gemini hallucinates and returns a list, unwrap it
        if isinstance(metadata, list) and len(metadata) > 0:
            metadata = metadata[0]

        print("\nMetadata extraction completed...")

        return metadata

    except Exception as e:
        print(f"Gemini API Error: {e}")
        return {}


def extract_policy_metadata(text, user_id="default_global"):
    """Extracts structured policy metadata (JSON) for the Master Index using Gemini."""
    print("\nExtracting policy metadata...")

    from src.utils.get_prompt import get_policy_extraction_prompt
    prompt = get_policy_extraction_prompt(text, user_id)

    try:
        response = _generate_content_with_retry(prompt)
        
        print("\n===== POLICY GEMINI USAGE =====")
        try:
            usage = response.usage_metadata
            print(usage)
            print("Prompt Tokens:", usage.prompt_token_count)
            print("Output Tokens:", usage.candidates_token_count)
            print("Total Tokens:", usage.total_token_count)
            calculate_gemini_cost(
                prompt_tokens=usage.prompt_token_count,
                output_tokens=usage.candidates_token_count,
                input_cost_per_million=0.25,
                output_cost_per_million=1.50
            )
        except Exception as e:
            print("Usage metadata unavailable:", e)
        print("========================\n")   

        if not response.text:
            return {"error": "Empty response from Gemini"}

        output = response.text.strip()
        if "```json" in output:
            output = output.replace("```json", "")
        if "```" in output:
            output = output.replace("```", "")
        output = output.strip()

        metadata = json.loads(output)
        
        # Safety net: If Gemini returns a single dict instead of a list, wrap it in a list
        if isinstance(metadata, dict):
            metadata = [metadata]
            
        print("\nPolicy Metadata extraction completed...")
        return metadata

    except Exception as e:
        print(f"Gemini Policy API Error: {e}")
        return {}
