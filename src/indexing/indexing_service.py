from dotenv import load_dotenv
import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents import SearchClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchFieldDataType
)
import json

load_dotenv()

endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
admin_key = os.getenv("AZURE_SEARCH_API_ADMIN_KEY")
query_key = os.getenv("AZURE_SEARCH_API_QUERY_KEY")

# creating search client
client = SearchIndexClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(admin_key)
)

# #defining required fields
fields = [
    SimpleField(name="id", type=SearchFieldDataType.String, key=True),

    SearchableField(
        name="file_name",
        type=SearchFieldDataType.String
        
    ),

    SearchableField(
        name="content",
        type=SearchFieldDataType.String
    ),

    SearchableField(
        name="document_type",
        type=SearchFieldDataType.String
    ),

    SimpleField(
        name="amount",
        type=SearchFieldDataType.Double,
        filterable=True,
        sortable=True
    ),

    SearchableField(
        name="invoice_number",
        type=SearchFieldDataType.String
    ),
    SearchableField(
        name="sharepoint_url",
        type=SearchFieldDataType.String
    ),
    
    SimpleField(
    name="date",
    type=SearchFieldDataType.DateTimeOffset,
    filterable=True,
    sortable=True
    )
]
search_client = SearchClient(
    endpoint=endpoint,
    index_name="documents-index",
    credential=AzureKeyCredential(admin_key)
)

documents = [
    {
        "id": "1",
        "file_name": "invoice_001.pdf",
        "content": "White Forest Cake 1kg amount 1000",
        "document_type": "invoice",
        "amount": 1000,
        "date": "2026-03-31T00:00:00Z",
        "sharepoint_url": "https://sharepoint.com/invoice1"
    },
    {
        "id": "2",
        "file_name": "claim_001.pdf",
        "content": "Water damage insurance claim amount 5000",
        "document_type": "claim",
        "amount": 5000,
        "date": "2026-04-01T00:00:00Z",
        "sharepoint_url": "https://sharepoint.com/claim1"
    }
]

result = search_client.upload_documents(documents)


def createIndex():
    index = SearchIndex(
    name="documents-index",
    fields=fields
    )

    client.create_index(index)






def uploadDocuments():
    result = search_client.upload_documents(documents)
    print("Documents uploaded")
    print(
    json.dumps(
        [dict(item) for item in result],
        indent=4
    )
)


uploadDocuments()