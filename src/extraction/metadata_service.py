import json

from google import genai

from src.config.config import OPENAI_API_KEY
from src.utils.metadata_prompt import get_metadata_extraction_prompt


client = genai.Client(
    api_key=OPENAI_API_KEY
)





def extract_metadata(text):
    print("\nExtracting metadata...")

    prompt = get_metadata_extraction_prompt(text)

    try:

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        output = response.text.strip()

        if "```json" in output:
            output = output.replace("```json", "")

        if "```" in output:
            output = output.replace("```", "")

        output = output.strip()
        
        print("\nMetadata extraction completed...")

        return json.loads(output)

    except Exception as e:

        return {
            "error": str(e)
        }





    

    

   