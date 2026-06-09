from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

from config import (
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_ADMIN_KEY
)


def upload_documents(documents):
    search_client = SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        index_name="documents-index",
        credential=AzureKeyCredential(AZURE_SEARCH_ADMIN_KEY)
    )

    return search_client.upload_documents(documents)