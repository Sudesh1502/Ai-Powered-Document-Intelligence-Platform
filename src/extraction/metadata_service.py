"""
This file handles metadata extraction from text using a Generative AI model.
"""
import json

from google import genai

from src.config.config import GEMINI_API_KEY
from src.utils.get_prompt import get_metadata_extraction_prompt
from tenacity import retry, stop_after_attempt, wait_exponential


client = genai.Client(
    api_key=GEMINI_API_KEY
)

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=10))
def _generate_content_with_retry(prompt):
    """Helper function to call Gemini API with automatic retries on failure."""
    return client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )


def extract_metadata(text):
    """Extracts structured metadata (JSON) from raw text using Gemini."""
    print("\nExtracting metadata...")

    prompt = get_metadata_extraction_prompt(text)

    try:

        #we are trying to retry the meta data extraction whenever server is busy of gemini.
        response = _generate_content_with_retry(prompt)

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

        print("\nMetadata extraction completed...")

        return metadata

    except Exception as e:
        print(f"Gemini API Error: {e}")
        return {}
