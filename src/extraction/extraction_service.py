"""
This file handles text extraction (OCR) using Azure Document Intelligence.
"""
import json
from pathlib import Path

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from src.config.config import (AZURE_OCR_ENDPOINT, AZURE_OCR_API_KEY)





def get_client():
    """Initializes and returns the Azure Document Intelligence client."""
    return DocumentIntelligenceClient(
        endpoint=AZURE_OCR_ENDPOINT,
        credential=AzureKeyCredential(AZURE_OCR_API_KEY)
    )


def extract_text(file_path):
    """Extracts text from a given document using Azure OCR."""
    print("\nExtraction service hit, text is being extracted.")
    client = get_client()

    with open(file_path, "rb") as file:
        poller = client.begin_analyze_document(
            "prebuilt-read",
            body=file
        )
        
    print("\nExtraction completed...")

    return poller.result()
    
    


def calculate_confidence(result):
    """Calculates the average confidence score from the OCR result."""
    confidences = []

    for page in result.pages:
        if page.words:
            for word in page.words:
                confidences.append(word.confidence)

    if not confidences:
        return 0

    return sum(confidences) / len(confidences)



