import os
import uuid
import datetime
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from src.config.config import AZURE_STORAGE_CONNECTION_STRING

# The name of the container where all processed files will be stored
CONTAINER_NAME = "processed-documents"

def _get_blob_service_client():
    if not AZURE_STORAGE_CONNECTION_STRING:
        raise ValueError("AZURE_STORAGE_CONNECTION_STRING is not set.")
    return BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)

def ensure_container_exists():
    """Ensures the blob container exists, creates it if it doesn't."""
    try:
        blob_service_client = _get_blob_service_client()
        container_client = blob_service_client.get_container_client(CONTAINER_NAME)
        if not container_client.exists():
            container_client.create_container()
            print(f"[BlobService] Created container: {CONTAINER_NAME}")
    except Exception as e:
        print(f"[BlobService] Error checking/creating container: {e}")

def upload_to_blob(file_bytes: bytes, original_filename: str) -> str:
    """
    Uploads raw file bytes to Azure Blob Storage and returns a unique blob name.
    
    Args:
        file_bytes: The raw bytes of the file.
        original_filename: The original name of the file (to extract extension).
        
    Returns:
        The generated unique blob name in Azure Storage.
    """
    ensure_container_exists()
    
    # Generate a unique name to prevent accidental overwrites
    extension = original_filename.split('.')[-1] if '.' in original_filename else 'bin'
    unique_blob_name = f"{uuid.uuid4()}.{extension}"
    
    try:
        blob_service_client = _get_blob_service_client()
        blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=unique_blob_name)
        
        # Upload the file
        blob_client.upload_blob(file_bytes, overwrite=True)
        print(f"[BlobService] Uploaded {original_filename} as {unique_blob_name} to Blob Storage.")
        return unique_blob_name
    except Exception as e:
        print(f"[BlobService] Failed to upload blob: {e}")
        return ""

def generate_sas_url(blob_name: str, expiry_hours: int = 1) -> str:
    """
    Generates a secure SAS URL to temporarily access the blob.
    
    Args:
        blob_name: The name of the blob in the container.
        expiry_hours: How long the link should be valid for (default 1 hour).
        
    Returns:
        The full HTTP URL with the SAS token appended.
    """
    if not blob_name:
        return ""
        
    try:
        blob_service_client = _get_blob_service_client()
        account_name = blob_service_client.account_name
        account_key = blob_service_client.credential.account_key
        
        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=CONTAINER_NAME,
            blob_name=blob_name,
            account_key=account_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.datetime.utcnow() + datetime.timedelta(hours=expiry_hours)
        )
        
        # Construct the full URL
        blob_url = f"https://{account_name}.blob.core.windows.net/{CONTAINER_NAME}/{blob_name}?{sas_token}"
        return blob_url
    except Exception as e:
        print(f"[BlobService] Failed to generate SAS URL: {e}")
        return ""

def delete_blob(blob_name: str) -> bool:
    """
    Deletes a blob from the Azure container.
    """
    if not blob_name:
        return False
        
    try:
        blob_service_client = _get_blob_service_client()
        blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=blob_name)
        blob_client.delete_blob()
        print(f"[BlobService] Deleted blob: {blob_name}")
        return True
    except Exception as e:
        print(f"[BlobService] Failed to delete blob {blob_name}: {e}")
        return False
