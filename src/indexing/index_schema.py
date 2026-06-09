from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchFieldDataType
)

# #defining required fields
Fields = [
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