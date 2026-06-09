import json
from pathlib import Path

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from config import (AZURE_OCR_ENDPOINT, AZURE_OCR_API_KEY)

BASE_DIR = Path(__file__).resolve().parents[2]

FILE_PATH = BASE_DIR / "data" / "filled accord form five.pdf"



def get_client():
    return DocumentIntelligenceClient(
        endpoint=AZURE_OCR_ENDPOINT,
        credential=AzureKeyCredential(AZURE_OCR_API_KEY)
    )


def extract_text(pdf_path):
    client = get_client()

    with open(pdf_path, "rb") as file:
        poller = client.begin_analyze_document(
            "prebuilt-read",
            body=file
        )

    return poller.result()


def main():
    result = extract_text(FILE_PATH)

    print(json.dumps(result.as_dict(), indent=2))


if __name__ == "__main__":
    main()