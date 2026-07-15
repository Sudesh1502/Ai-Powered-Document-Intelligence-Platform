import json
from azure.data.tables import TableServiceClient
from src.config.config import AZURE_STORAGE_CONNECTION_STRING

def get_table_client():
    """Initializes and returns the TableClient for AppConfiguration."""
    if not AZURE_STORAGE_CONNECTION_STRING:
        print("Warning: AZURE_STORAGE_CONNECTION_STRING is not set. Custom attributes will not persist.")
        return None
        
    try:
        service_client = TableServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        table_client = service_client.create_table_if_not_exists("AppConfiguration")
        return table_client
    except Exception as e:
        print(f"Error connecting to Azure Table Storage: {e}")
        return None

def load_custom_attributes(user_id="default_global"):
    """Loads custom attributes for the given user_id from Azure Table Storage."""
    client = get_table_client()
    if not client:
        return []
        
    try:
        entity = client.get_entity(partition_key="CustomAttributes", row_key=user_id)
        attributes_json = entity.get("attributes_json", "[]")
        return json.loads(attributes_json)
    except Exception as e:
        # ResourceNotFoundError is expected if the user has no config yet
        if "ResourceNotFound" not in str(e):
            print(f"Error loading custom attributes: {e}")
        return []

def save_custom_attributes(attrs, user_id="default_global"):
    """Saves custom attributes for the given user_id to Azure Table Storage."""
    client = get_table_client()
    if not client:
        return False
        
    try:
        entity = {
            "PartitionKey": "CustomAttributes",
            "RowKey": user_id,
            "attributes_json": json.dumps(attrs)
        }
        client.upsert_entity(entity)
        return True
    except Exception as e:
        print(f"Error saving custom attributes: {e}")
        return False
