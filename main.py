"""
Main script that orchestrates the entire document processing pipeline: ingestion, extraction, and indexing.
"""
import uuid
from pathlib import Path
from src.ingestion.ingestion_service import get_unprocessed_documents
from src.extraction.extraction_service import calculate_confidence
from src.extraction.extraction_service import extract_text
from src.extraction.metadata_service import extract_metadata
from src.indexing.indexing_service import create_index
from src.indexing.upload_document_service import upload_documents
from src.utils.logger import log_document_status
import json

# Set up the paths to grab files from our local 'data' folder
BASE_DIR = Path(__file__).resolve().parent
RAW_DATA_DIR = BASE_DIR / "data"

# Pull in all the raw files (this automatically filters out the bad extensions or huge files)
documents = get_unprocessed_documents(RAW_DATA_DIR)

# Bail out early if there's nothing to process
if not documents:
    print("\nDirectory is empty")
    exit()

print("\nprocessing documents for extraction")
print(f"\nTotal {len(documents)} found.")

# We're just looping through the first 5 docs to save time/API costs during testing
for doc in documents[:5]:
    file_name = Path(doc).name
    url = str(Path(doc).resolve())
    
    try:
        print(f"\nProcessing {file_name}...")
        
        # Step 1: Send the document to Azure to read the raw text
        result = extract_text(doc)
        confidence = calculate_confidence(result)
        
        # Step 2: Pass that messy text to Gemini to pull out the structured data we actually care about
        metadata = extract_metadata(result.content)
        
        # Catch it early if Gemini failed to generate proper JSON
        if "error" in metadata:
            raise Exception(f"Metadata extraction failed: {metadata['error']}")

        # Step 3: Package everything up into the exact shape Azure Search expects
        indexed_document = {
            "id": str(uuid.uuid4()),  # Need a unique ID for the database
            "file_name": file_name,
            "document_type": metadata.get("document_type"),
            "document_title": metadata.get("document_title"),
            "content": result.content,  # Storing the full raw text just in case
            "document_number": metadata.get("document_number"),
            "entity_name": metadata.get("entity_name"),
            "amount": metadata.get("amount"),
            "document_date": metadata.get("document_date"),
            "page_count": len(result.pages),
            "confidence": confidence,
            "metadata": json.dumps(metadata.get("metadata", {})),  # Azure needs this nested object as a string
            "sharepoint_url": ""  # Leaving this blank until we hook up SharePoint
        }
        
        # Step 4: Push the final payload up to the Azure Search index
        upload_result = upload_documents([indexed_document])
        
        # Log the success so we have a record
        log_document_status(
            file_name=file_name,
            url=url,
            status="Completed",
            note="File index created successfully"
        )
        print(f"Successfully processed and indexed {file_name}")

    except Exception as e:
        # Log the failure so we can debug exactly which file choked
        error_msg = str(e)
        log_document_status(
            file_name=file_name,
            url=url,
            status="Failed",
            note=error_msg
        )
        print(f"Failed to process {file_name}: {error_msg}")

# Note: If you get a 'Resource Not Found' error, uncomment these to create the Azure bucket first!
# index = create_index()
# print(index)