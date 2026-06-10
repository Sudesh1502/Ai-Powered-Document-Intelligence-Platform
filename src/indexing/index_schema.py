from azure.search.documents.indexes.models import (
    SimpleField,
    SearchableField,
    SearchFieldDataType
)

FIELDS = [

    
    SimpleField(
        name="id",
        type=SearchFieldDataType.String,
        key=True
    ),

    
    SearchableField(
        name="file_name",
        type=SearchFieldDataType.String
    ),

    SearchableField(
        name="document_type",
        type=SearchFieldDataType.String
    ),

    
    SearchableField(
        name="content",
        type=SearchFieldDataType.String
    ),

   
    SearchableField(
        name="document_number",
        type=SearchFieldDataType.String
    ),

    SearchableField(
        name="entity_name",
        type=SearchFieldDataType.String
    ),

    SimpleField(
        name="amount",
        type=SearchFieldDataType.Double,
        filterable=True,
        sortable=True
    ),

    SimpleField(
        name="document_date",
        type=SearchFieldDataType.DateTimeOffset,
        filterable=True,
        sortable=True
    ),

    
    SimpleField(
        name="page_count",
        type=SearchFieldDataType.Int32
    ),

    SimpleField(
        name="confidence",
        type=SearchFieldDataType.Double
    ),

    
    SearchableField(
        name="metadata",
        type=SearchFieldDataType.String
    ),

    
    SearchableField(
        name="sharepoint_url",
        type=SearchFieldDataType.String
    )
]