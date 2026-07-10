import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import SearchIndex

from src.config.config import AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_ADMIN_KEY
from src.indexing.index_schema import FIELDS, SEMANTIC_SEARCH

def create_generic_index():
    print("Connecting to Azure AI Search...")
    client = SearchIndexClient(AZURE_SEARCH_ENDPOINT, AzureKeyCredential(AZURE_SEARCH_ADMIN_KEY))
    
    try:
        print("Deleting existing generic-documents-index...")
        client.delete_index("generic-documents-index")
        print("Deleted.")
    except Exception:
        pass
    
    index = SearchIndex(
        name="generic-documents-index",
        fields=FIELDS,
        semantic_search=SEMANTIC_SEARCH
    )
    print("Creating/Updating generic-documents-index...")
    client.create_or_update_index(index)
    print("Successfully created generic-documents-index!")

if __name__ == "__main__":
    create_generic_index()
