"""
This file handles uploading structured documents to the Azure search index.
"""
import json
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient

from src.config.config import (
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_ADMIN_KEY
)

# The exact set of fields defined in index_schema.py (generic-documents-index).
# Any field NOT in this set is silently dropped before upload to prevent
# Azure Search 400 errors caused by unrecognised top-level properties.
_GENERIC_SCHEMA_FIELDS = {
    "id", "file_name", "document_type", "document_title",
    "content", "document_number", "entity_name",
    "document_date", "page_count", "confidence",
    "metadata", "sharepoint_url"
}

# Internal-only keys that should never be stored inside the metadata JSON blob.
# They are useful for de-duplication at ingest time but pollute the search index.
_METADATA_STRIP_KEYS = {
    "flagged_tokens", "sha256_signature", "minhash_signature", "phash_signature",
    "user_tracking"
}


def upload_documents(documents, index_name="generic-documents-index"):
    """Uploads a list of formatted documents to the Azure search index.

    Performs two levels of sanitization before sending to Azure Search:
    1. Top-level: only schema-defined fields are forwarded (whitelist).
    2. metadata blob: internal-only keys are stripped from the JSON string.
    """
    print(f"\nUploading documents to index: {index_name}...")

    sanitized_docs = []
    for doc in documents:
        # For the policy index we don't enforce the generic whitelist because
        # its schema is different — we only strip the known-bad keys.
        if index_name == "generic-documents-index":
            # Step 1: Whitelist — keep only schema fields
            doc_copy = {k: v for k, v in doc.items() if k in _GENERIC_SCHEMA_FIELDS}
        else:
            # Policy index — copy everything but remove obvious rogue fields
            doc_copy = {k: v for k, v in doc.items()
                        if k not in {"review_status", "review_reason", "status",
                                     "flagged_tokens", "sha256_signature",
                                     "minhash_signature", "phash_signature",
                                     "user_tracking", "queue_date", "source"}}

        # Step 2: Strip internal-only keys from the metadata JSON blob
        if "metadata" in doc_copy and doc_copy["metadata"]:
            try:
                meta = json.loads(doc_copy["metadata"]) if isinstance(doc_copy["metadata"], str) else doc_copy["metadata"]
                for key in _METADATA_STRIP_KEYS:
                    meta.pop(key, None)
                doc_copy["metadata"] = json.dumps(meta)
            except Exception:
                pass  # If metadata is malformed, leave it as-is

        sanitized_docs.append(doc_copy)

    search_client = SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        index_name=index_name,
        credential=AzureKeyCredential(AZURE_SEARCH_ADMIN_KEY)
    )
    print("\nIndex uploaded!")
    return search_client.upload_documents(sanitized_docs)