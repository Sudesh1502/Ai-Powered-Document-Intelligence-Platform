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


def extract_text(file_input, extension=None):
    """Extracts text from a given document using Azure OCR. Accepts a file path or raw bytes."""
    print("\nExtraction service hit, text is being extracted.")
    client = get_client()

    content_type = None
    if extension:
        ext = extension.lower()
        if ext == '.pdf':
            content_type = 'application/pdf'
        elif ext in ['.docx', '.doc']:
            content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        elif ext in ['.jpg', '.jpeg']:
            content_type = 'image/jpeg'
        elif ext == '.png':
            content_type = 'image/png'

    if isinstance(file_input, str):
        with open(file_input, "rb") as file:
            kwargs = {"body": file}
            if content_type:
                kwargs["content_type"] = content_type
                
            poller = client.begin_analyze_document(
                "prebuilt-read",
                **kwargs
            )
    else:
        # Assuming file_input is raw bytes
        kwargs = {"body": file_input}
        if content_type:
            kwargs["content_type"] = content_type
            
        poller = client.begin_analyze_document(
            "prebuilt-read",
            **kwargs
        )
        
    print("\nExtraction completed...")

    # Added a timeout to prevent infinite hangs
    return poller.result(timeout=120)
    
    






