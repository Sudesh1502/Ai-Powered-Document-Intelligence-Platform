"""
This file handles the creation of the search index in Azure AI Search.
"""
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import SearchIndex

from src.config.config import (
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_ADMIN_KEY
)
from src.indexing.index_schema import FIELDS, SEMANTIC_SEARCH


def create_index():
    """Creates the generic documents index in Azure AI Search."""
    client = SearchIndexClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        credential=AzureKeyCredential(AZURE_SEARCH_ADMIN_KEY)
    )

    index = SearchIndex(
        name="generic-documents-index",
        fields=FIELDS,
        semantic_search=SEMANTIC_SEARCH
    )

    return client.create_index(index)