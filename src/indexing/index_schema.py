from azure.search.documents.indexes.models import (
    SimpleField,
    SearchableField,
    SearchFieldDataType,
    SemanticConfiguration,
    SemanticPrioritizedFields,
    SemanticField,
    SemanticSearch
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
        name="document_title",
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

# Define how the Semantic Ranker should interpret our fields
semantic_config = SemanticConfiguration(
    name="default-semantic-config",
    prioritized_fields=SemanticPrioritizedFields(
        title_field=SemanticField(field_name="document_title"),
        content_fields=[SemanticField(field_name="content")],
        keywords_fields=[
            SemanticField(field_name="document_type"),
            SemanticField(field_name="entity_name"),
            SemanticField(field_name="document_number")
        ]
    )
)

# Create the semantic search definition that we will attach to the index
SEMANTIC_SEARCH = SemanticSearch(configurations=[semantic_config])