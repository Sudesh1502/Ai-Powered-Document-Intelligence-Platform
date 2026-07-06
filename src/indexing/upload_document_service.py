"""
This file handles uploading structured documents to the Azure search index.
"""
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

from src.config.config import (
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_ADMIN_KEY
)


def upload_documents(documents):
    """Uploads a list of formatted documents to the Azure search index."""
    print("\nUploading documents to index...")
    search_client = SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        index_name="generic-documents-index",
        credential=AzureKeyCredential(AZURE_SEARCH_ADMIN_KEY)
    )
    print("\nIndex uploaded!")
    return search_client.upload_documents(documents)