import os
from azure.data.tables import TableServiceClient
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

def clear_azure_tables(connection_string: str):
    print("\n--- Clearing Azure Table Storage ---")
    try:
        table_service_client = TableServiceClient.from_connection_string(connection_string)
        tables = table_service_client.list_tables()
        
        for table in tables:
            table_name = table.name
            if table_name.lower() == "users":
                print(f"[!] Skipping 'Users' table (data preserved as requested).")
                continue
                
            print(f"[~] Clearing table: {table_name}...")
            table_client = table_service_client.get_table_client(table_name=table_name)
            
            # Query all entities in the table
            try:
                entities = list(table_client.query_entities(query_filter=""))
                if not entities:
                    print(f"    Table {table_name} is already empty.")
                    continue
                
                print(f"    Found {len(entities)} entities. Deleting...")
                for entity in entities:
                    partition_key = entity.get("PartitionKey")
                    row_key = entity.get("RowKey")
                    if partition_key and row_key:
                        table_client.delete_entity(partition_key=partition_key, row_key=row_key)
                print(f"[*] Cleared all entities from table: {table_name}")
            except Exception as e:
                print(f"[-] Failed to clear table {table_name}: {e}")
                
    except Exception as e:
        print(f"[-] Error connecting to Azure Table Storage: {e}")

def clear_azure_blobs(connection_string: str):
    print("\n--- Clearing Azure Blob Storage ---")
    try:
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        containers = blob_service_client.list_containers()
        
        for container in containers:
            container_name = container.name
            print(f"[~] Clearing container: {container_name}...")
            container_client = blob_service_client.get_container_client(container_name)
            
            try:
                blobs = list(container_client.list_blobs())
                if not blobs:
                    print(f"    Container {container_name} is already empty.")
                    continue
                    
                print(f"    Found {len(blobs)} blobs. Deleting...")
                for blob in blobs:
                    container_client.delete_blob(blob.name)
                    print(f"    [-] Deleted blob: {blob.name}")
                print(f"[*] Cleared all blobs from container: {container_name}")
            except Exception as e:
                print(f"[-] Failed to clear blobs in container {container_name}: {e}")
                
    except Exception as e:
        print(f"[-] Error connecting to Azure Blob Storage: {e}")

def main():
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if not connection_string:
        print("[-] Error: AZURE_STORAGE_CONNECTION_STRING is not set in your .env file.")
        return
        
    print("WARNING: This action will delete ALL records in your Azure Tables (except 'Users')")
    print("and ALL files in your Azure Blob Storage containers.")
    confirm = input("Are you absolutely sure you want to proceed? (yes/no): ").strip().lower()
    
    if confirm == "yes":
        clear_azure_tables(connection_string)
        clear_azure_blobs(connection_string)
        print("\n[+] Cleanup process finished.")
    else:
        print("[*] Operation cancelled.")

if __name__ == "__main__":
    main()
