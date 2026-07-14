import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SimpleField, SearchableField, SearchFieldDataType,
    SemanticConfiguration, SemanticPrioritizedFields, SemanticField, SemanticSearch
)

from src.config.config import AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_ADMIN_KEY

def create_master_index():
    print("Connecting to Azure AI Search...")
    client = SearchIndexClient(AZURE_SEARCH_ENDPOINT, AzureKeyCredential(AZURE_SEARCH_ADMIN_KEY))
    
    try:
        print("Deleting existing policy-master-index...")
        client.delete_index("policy-master-index")
        print("Deleted.")
    except Exception:
        pass
    
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="policy_number", type=SearchFieldDataType.String),
        SearchableField(name="insured_name", type=SearchFieldDataType.String),
        SearchableField(name="class_of_business", type=SearchFieldDataType.String),
        SimpleField(name="policy_effective_date", type=SearchFieldDataType.DateTimeOffset, filterable=True),
        SimpleField(name="policy_expiration_date", type=SearchFieldDataType.DateTimeOffset, filterable=True),
        SearchableField(name="risk_locations", collection=True),
        SimpleField(name="policy_limit", type=SearchFieldDataType.Double, filterable=True, sortable=True),
        SearchableField(name="sub_limits", collection=True),
        SimpleField(name="deductible_excess", type=SearchFieldDataType.Double, filterable=True),
        SearchableField(name="relevant_clauses", collection=True),
        SearchableField(name="exclusions", collection=True),
        SearchableField(name="notification_conditions", type=SearchFieldDataType.String),
        SearchableField(name="file_name", type=SearchFieldDataType.String),
        SearchableField(name="sharepoint_url", type=SearchFieldDataType.String),
        SearchableField(name="metadata", type=SearchFieldDataType.String)
    ]
    
    semantic_config = SemanticConfiguration(
        name="policy-semantic-config",
        prioritized_fields=SemanticPrioritizedFields(
            title_field=SemanticField(field_name="policy_number"),
            content_fields=[
                SemanticField(field_name="relevant_clauses"),
                SemanticField(field_name="exclusions")
            ],
            keywords_fields=[
                SemanticField(field_name="insured_name"),
                SemanticField(field_name="class_of_business")
            ]
        )
    )
    semantic_search = SemanticSearch(configurations=[semantic_config])
    
    index = SearchIndex(name="policy-master-index", fields=fields, semantic_search=semantic_search)
    print("Creating/Updating policy-master-index...")
    client.create_or_update_index(index)
    print("Successfully created policy-master-index!")

if __name__ == "__main__":
    create_master_index()
