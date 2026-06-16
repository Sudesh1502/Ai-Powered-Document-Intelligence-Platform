"""
This file handles metadata extraction from text using a Generative AI model.
"""
import json

from google import genai

from src.config.config import OPENAI_API_KEY
from utils.get_prompt import get_metadata_extraction_prompt


client = genai.Client(
    api_key=OPENAI_API_KEY
)



def extract_metadata(text):
    """Extracts structured metadata (JSON) from raw text using Gemini."""
    print("\nExtracting metadata...")

    prompt = get_metadata_extraction_prompt(text)

    try:

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

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

        return {
            "error": str(e)
        }
