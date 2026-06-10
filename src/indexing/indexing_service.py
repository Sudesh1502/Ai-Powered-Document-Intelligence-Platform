from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import SearchIndex

from src.config.config import (
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_ADMIN_KEY
)
from index_schema import FIELDS


def create_index():
    client = SearchIndexClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        credential=AzureKeyCredential(AZURE_SEARCH_ADMIN_KEY)
    )

    index = SearchIndex(
        name="documents-index",
        fields=FIELDS
    )

    client.create_index(index)