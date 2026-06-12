
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

BASE_DIR = Path(__file__).resolve().parent
RAW_DATA_DIR = BASE_DIR / "data"

documents = get_unprocessed_documents(RAW_DATA_DIR)

if not documents:
    print("\nDirectory is empty")
    exit()

print("\nprocessing documents for extraction")
print(f"\nTotal {len(documents)} found.")

for doc in documents[:5]:
    file_name = Path(doc).name
    url = str(Path(doc).resolve())
    
    try:
        print(f"\nProcessing {file_name}...")
        
        result = extract_text(doc)
        confidence = calculate_confidence(result)
        metadata = extract_metadata(result.content)
        
        if "error" in metadata:
            raise Exception(f"Metadata extraction failed: {metadata['error']}")

        indexed_document = {
            "id": str(uuid.uuid4()),
            "file_name": file_name,
            "document_type": metadata.get("document_type"),
            "document_title": metadata.get("document_title"),
            "content": result.content,
            "document_number": metadata.get("document_number"),
            "entity_name": metadata.get("entity_name"),
            "amount": metadata.get("amount"),
            "document_date": metadata.get("document_date"),
            "page_count": len(result.pages),
            "confidence": confidence,
            "metadata": json.dumps(metadata.get("metadata", {})),
            "sharepoint_url": ""
        }
        
        upload_result = upload_documents([indexed_document])
        
        # Log success
        log_document_status(
            file_name=file_name,
            url=url,
            status="Completed",
            note="File index created successfully"
        )
        print(f"Successfully processed and indexed {file_name}")

    except Exception as e:
        # Log failure
        error_msg = str(e)
        log_document_status(
            file_name=file_name,
            url=url,
            status="Failed",
            note=error_msg
        )
        print(f"Failed to process {file_name}: {error_msg}")


# index = create_index()
# print(index)