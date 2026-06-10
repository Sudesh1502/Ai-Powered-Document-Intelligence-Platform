import json

from google import genai

from src.config.config import GOOGLE_API_KEY


client = genai.Client(
    api_key=GOOGLE_API_KEY
)


def ocr_result_to_text(result):

    text_lines = []

    for page in result.pages:

        if page.lines:

            for line in page.lines:
                text_lines.append(line.content)

    return "\n".join(text_lines)


def extract_metadata(text):

    prompt = f"""
You are a document understanding AI.

Extract ONLY:

- document_type
- metadata

Return STRICT JSON:

{{
    "document_type": "...",
    "metadata": {{
        "key": "value"
    }}
}}

Rules:
- Fix obvious OCR mistakes
- Use snake_case keys
- No explanations
- Return valid JSON only

TEXT:
{text[:3000]}
"""

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

        return json.loads(output)

    except Exception as e:

        return {
            "error": str(e)
        }
    
#Temporary main function for testing BAAD ME CHANGE KARENGE TO MAIN WALA MAIN
if __name__ == "__main__":

    from src.extraction.extraction_service import (
        extract_text,
        FILE_PATH
    )

    result = extract_text(FILE_PATH)

    text = ocr_result_to_text(result)

    metadata = extract_metadata(text)

    print(json.dumps(metadata, indent=2))
