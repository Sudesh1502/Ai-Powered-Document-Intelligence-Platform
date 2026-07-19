import uuid
import json
from datetime import datetime, timezone, timedelta
from azure.data.tables import TableServiceClient
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from src.config.config import AZURE_STORAGE_CONNECTION_STRING

TABLE_NAME = "reviewqueue"
PARTITION_KEY = "Queue"

def _get_table_client():
    if not AZURE_STORAGE_CONNECTION_STRING:
        print("[-] AZURE_STORAGE_CONNECTION_STRING is not set.")
        return None
        
    try:
        service_client = TableServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        try:
            service_client.create_table(TABLE_NAME)
        except ResourceExistsError:
            pass
        return service_client.get_table_client(TABLE_NAME)
    except Exception as e:
        print(f"[-] Failed to connect to Azure Table Storage: {e}")
        return None

def load_review_documents():
    """Loads all documents currently in the review queue from Azure Tables."""
    client = _get_table_client()
    if not client:
        return []
        
    documents = []
    try:
        # Query all entities in the Queue partition and sort by Azure's Timestamp
        entities = list(client.query_entities(query_filter=f"PartitionKey eq '{PARTITION_KEY}'"))
        entities.sort(key=lambda x: x.get("Timestamp", datetime.min), reverse=False)
        
        for entity in entities:
            # Reconstruct the document dictionary
            doc = dict(entity)
            
            # Extract Azure's UTC Timestamp, convert to IST, and store for frontend display
            if "Timestamp" in doc:
                try:
                    utc_time = doc["Timestamp"]
                    ist_time = utc_time.astimezone(timezone.utc) + timedelta(hours=5, minutes=30)
                    doc["queue_date"] = ist_time.strftime("%Y-%m-%d %I:%M %p IST")
                except Exception:
                    doc["queue_date"] = "Unknown"
            
            doc["id"] = doc.pop("RowKey")
            # Remove Azure Table specific metadata
            doc.pop("PartitionKey", None)
            doc.pop("Timestamp", None)
            doc.pop("odata.etag", None)
            
            # Deserialize nested JSON strings back into dictionaries/lists if necessary
            for k, v in doc.items():
                if isinstance(v, str) and (v.startswith("{") or v.startswith("[")):
                    try:
                        doc[k] = json.loads(v)
                    except json.JSONDecodeError:
                        pass
            
            documents.append(doc)
    except Exception as e:
        print(f"[-] Failed to load review documents: {e}")
        
    return documents

def save_review_documents(documents):
    """Deprecated: Azure Tables don't require bulk saving. Kept for signature compatibility."""
    pass

def add_review_document(document: dict):
    """Adds a new document to the Azure Table review queue."""
    client = _get_table_client()
    if not client:
        return
        
    # Ensure ID exists
    doc_id = document.get("id", str(uuid.uuid4()))
    
    # Prepare the entity payload
    entity = {
        "PartitionKey": PARTITION_KEY,
        "RowKey": doc_id,
    }
    
    # Azure Table Storage doesn't support nested dicts/lists, so we serialize them
    for k, v in document.items():
        if k == "id":
            continue
        if isinstance(v, (dict, list)):
            entity[k] = json.dumps(v, ensure_ascii=False)
        elif v is None:
            entity[k] = "" # Tables don't like None types
        else:
            entity[k] = str(v)
            
    try:
        client.upsert_entity(entity=entity)
        print(f"[+] Document {doc_id} routed to Azure Table Review Queue.")
    except Exception as e:
        print(f"[-] Failed to add review document: {e}")

def remove_review_document(document_id_or_name: str):
    """Removes a document from the Azure Table review queue by ID or filename."""
    client = _get_table_client()
    if not client:
        return
        
    # First, try to delete by RowKey (assuming document_id_or_name is the UUID)
    try:
        client.delete_entity(partition_key=PARTITION_KEY, row_key=document_id_or_name)
        print(f"[+] Document {document_id_or_name} removed from Review Queue.")
        return
    except ResourceNotFoundError:
        pass
        
    # If it wasn't the ID, maybe it was the file_name (backwards compatibility)
    try:
        entities = client.query_entities(query_filter=f"PartitionKey eq '{PARTITION_KEY}' and file_name eq '{document_id_or_name}'")
        for entity in entities:
            client.delete_entity(partition_key=PARTITION_KEY, row_key=entity["RowKey"])
            print(f"[+] Document {document_id_or_name} removed from Review Queue.")
    except Exception as e:
        print(f"[-] Failed to remove review document by name: {e}")