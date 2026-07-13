
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
from datetime import datetime
from src.validation.validation_engine import validate_document_orchestrator
from src.utils.review_storage import add_review_document

BASE_DIR = Path(__file__).resolve().parent
RAW_DATA_DIR = BASE_DIR / "data"

documents = get_unprocessed_documents(RAW_DATA_DIR)

if not documents:
    print("\nDirectory is empty")
    exit()

print("\nprocessing documents for extraction")
print(f"\nTotal {len(documents)} found.")

for doc in documents[:2]:
    file_name = Path(doc).name
    url = str(Path(doc).resolve())
    
    start_time = datetime.now()
    try:
        print(f"\nProcessing {file_name}...")
        
        result = extract_text(doc)
        word_count = len(result.content.split()) if result.content else 0
        confidence = calculate_confidence(result)
        metadata = extract_metadata(result.content)
        if "error" in metadata:
            raise Exception(f"Metadata extraction failed: {metadata['error']}")
        #validating the data before indexing
        validation_results = validate_document_orchestrator(metadata)
        missing_fields = validation_results["missing"]
        invalid_fields = validation_results["invalid"]

        # if it misses ANY critical fields or has invalid formats, route it to Action Centre
        if len(missing_fields) > 0 or len(invalid_fields) > 0:
            reasons = []
            if missing_fields:
                reasons.append(f"Missing: {', '.join(missing_fields)}")
            if invalid_fields:
                reasons.append(f"Invalid Format: {', '.join(invalid_fields)}")
            reason_str = " | ".join(reasons)
            
            print(f"Validation failed for {file_name}. {reason_str}")
            
            # Add exactly what went wrong to the metadata so the user can see it in Action Centre
            metadata["file_name"] = file_name
            metadata["review_reason"] = f"Validation Failed - {reason_str}"
            metadata["status"] = "Needs Review"
            
            # Save it to the Action Centre queue
            add_review_document(metadata)
            
            # Log the failure
            log_document_status(
                file_name=file_name,
                url=url,
                status="Needs Review",
                note=f"Validation failed. {reason_str}",
                start_time=start_time,
                end_time=datetime.now(),
                word_count=word_count
            )
            
            # IMPORTANT: Use 'continue' or 'return' here to skip the Azure Search upload!
            continue
        
        # Cross Validation against Policy Master Index
        doc_type = metadata.get("document_type", "").lower()
        if doc_type in ["major claim", "claim form", "claim closure", "claim closure report", "claim settlement"]:
            from src.validation.cross_validation_service import cross_validate_claim
            breach_errors = cross_validate_claim(metadata)
            
            if breach_errors:
                reason_str = " | ".join(breach_errors)
                print(f"Policy Breach for {file_name}. {reason_str}")
                
                metadata["file_name"] = file_name
                metadata["review_reason"] = f"Policy Breach - {reason_str}"
                metadata["status"] = "Needs Review"
                
                add_review_document(metadata)
                
                log_document_status(
                    file_name=file_name,
                    url=url,
                    status="Needs Review",
                    note=f"Policy Breach. {reason_str}",
                    start_time=start_time,
                    end_time=datetime.now(),
                    word_count=word_count
                )
                continue
        
        
        raw_date = str(metadata.get("document_date", ""))
        formatted_date = None
        
        if raw_date and raw_date.strip() not in ["", "None"]:
            if "T" not in raw_date:
                formatted_date = f"{raw_date.strip()}T00:00:00Z"
            else:
                formatted_date = raw_date.strip()

        indexed_document = {
            "id": str(uuid.uuid4()),
            "file_name": file_name,
            "document_type": metadata.get("document_type"),
            "document_title": metadata.get("document_title"),
            "content": result.content,
            "document_number": metadata.get("document_number"),
            "entity_name": metadata.get("entity_name"),
            "document_date": formatted_date,
            "page_count": len(result.pages) if result.pages else 0,
            "confidence": confidence,
            "metadata": json.dumps(metadata.get("metadata", {})),
            "sharepoint_url": ""
        }
        
        upload_result = upload_documents([indexed_document])
        
        # Log success
        end_time = datetime.now()
        log_document_status(
            file_name=file_name,
            url=url,
            status="Completed",
            note="File index created successfully",
            start_time=start_time,
            end_time=end_time,
            word_count=word_count,
        )
        print(f"Successfully processed and indexed {file_name}")

    except Exception as e:
        # Log failure
        end_time = datetime.now()
        error_msg = str(e)
        log_document_status(
            file_name=file_name,
            url=url,
            status="Failed",
            note=error_msg,
            start_time=start_time,
            end_time=end_time
        )
        print(f"Failed to process {file_name}: {error_msg}")


