import time
import uuid
import datetime
import os
from src.ingestion.gmail_agent import GmailAgent
from src.extraction.extraction_service import extract_text
from src.extraction.metadata_service import extract_metadata
from src.indexing.duplicate_detection_service import DuplicateDetectionService
from src.indexing.upload_document_service import upload_documents
from src.validation.validation_engine import validate_document_orchestrator, validate_email_intent_match
from src.utils.review_storage import add_review_document
from src.utils.document_builder import build_document
from src.utils.logger import log_document_status
from src.utils.blob_service import upload_to_blob

class MockFile:
    def __init__(self, name):
        self.name = name

def process_email_attachment(email_body: str, attachment: dict, dedupe_service: DuplicateDetectionService):
    filename = attachment["filename"]
    file_bytes = attachment["data"]
    start_time = datetime.datetime.now()
    
    print(f"\n[GMAIL-WORKER] Processing attachment: {filename}")
    
    # Layer 1: Exact Duplicate Detection
    if dedupe_service.is_exact_duplicate(file_bytes):
        print(f"[GMAIL-WORKER] Exact duplicate detected for {filename}. Skipping.")
        return

    # Extract Text via OCR
    print(f"[GMAIL-WORKER] Extracting text...")
    try:
        extension = os.path.splitext(filename)[1].lower()
        ocr_result = extract_text(file_bytes, extension=extension)
        text = ocr_result.content if ocr_result else ""
        from src.utils.ocr_scoring import calculate_weighted_confidence
        ocr_analysis = calculate_weighted_confidence(ocr_result) if ocr_result else {}
        confidence = round(ocr_analysis.get("weighted_score", 0.0), 2)
        print(f"Confidence score: {confidence}")
        page_count = len(ocr_result.pages) if ocr_result and hasattr(ocr_result, "pages") else 1
    except Exception as e:
        print(f"[GMAIL-WORKER] Azure OCR failed: {e}")
        text = ""
        confidence = 0.0
        page_count = 1
        
    if not text:
        print(f"[GMAIL-WORKER] Failed to extract text from {filename}. Skipping.")
        return

    # Upload to Azure Blob Storage EARLY so that even rejected/duplicate documents can be previewed in the Action Centre
    unique_blob_name = upload_to_blob(file_bytes, filename)
    
    # Layer 2: Near-Duplicate Detection
    if dedupe_service.is_near_duplicate(text, file_bytes, filename):
        print(f"[GMAIL-WORKER] Near duplicate detected for {filename}. Routing to Action Centre.")
        metadata_review = {
            "id": str(uuid.uuid4()),
            "file_name": filename,
            "document_title": filename,
            "status": "Needs Review",
            "review_reason": "Near-Duplicate (Text/Visual Similarity)",
            "source": "Incoming Email",
            "sharepoint_url": unique_blob_name  # Injected here for the preview!
        }
        add_review_document(metadata_review)
        return

    # Extract Metadata via Gemini
    print(f"[GMAIL-WORKER] Extracting metadata via Gemini...")
    metadata = extract_metadata(text)
    metadata["source"] = "Incoming Email"
    metadata["flagged_tokens"] = ocr_analysis.get("flagged_tokens", []) if ocr_analysis else []
    
    # Layer 3: Data-Level Duplicate Detection
    if dedupe_service.is_data_level_duplicate(metadata):
        print(f"[GMAIL-WORKER] Data-level duplicate detected for {filename}. Routing to Action Centre.")
        metadata["file_name"] = filename
        metadata["status"] = "Needs Review"
        metadata["review_reason"] = "Data-Level Duplicate (Matching ID & Vendor)"
        metadata["sharepoint_url"] = unique_blob_name  # Injected here for the preview!
        add_review_document(metadata)
        log_document_status(
            file_name=filename, url="Gmail Ingestion", status="Needs Review",
            note="Data-Level Duplicate (Matching ID & Vendor)", start_time=start_time, end_time=datetime.datetime.now(), word_count=len(text.split()) if text else 0
        )
        return

    # OCR Confidence Validation
    from src.utils.review_service import get_review_status
    review_status = get_review_status(confidence, metadata)
    
    if review_status == "Failed":
        print(f"[GMAIL-WORKER] Rejecting document ({confidence}%). Confidence too low.")
        log_document_status(
            file_name=filename, url="Gmail Ingestion", status="Failed",
            note=f"Rejected due to extremely low confidence ({confidence}%)", start_time=start_time, end_time=datetime.datetime.now(), word_count=len(text.split()) if text else 0
        )
        return
    elif review_status != "Completed":
        print(f"[GMAIL-WORKER] Low confidence ({confidence}%). Routing to Action Centre.")
        metadata["file_name"] = filename
        metadata["status"] = "Needs Review"
        metadata["review_reason"] = f"Low OCR Confidence ({confidence}%)"
        add_review_document(metadata)
        log_document_status(
            file_name=filename, url="Gmail Ingestion", status="Needs Review",
            note=metadata["review_reason"], start_time=start_time, end_time=datetime.datetime.now(), word_count=len(text.split()) if text else 0
        )
        return

    # Structural Validation
    validation_results = validate_document_orchestrator(metadata)
    
    # Semantic Intent Validation (Email Body vs Attachment) - Temporarily Disabled
    # intent_validation = validate_email_intent_match(email_body, metadata)
    
    is_valid = len(validation_results["missing"]) == 0 and len(validation_results["invalid"]) == 0
    # and not intent_validation["is_mismatch"]
    
    # Inject Fingerprints into metadata blob
    metadata["sha256_signature"] = dedupe_service.generate_sha256_hash(file_bytes)
    metadata["minhash_signature"] = dedupe_service.generate_minhash(text)
    metadata["phash_signature"] = dedupe_service.generate_phash(file_bytes, filename)
    
    # Format document_date safely for Azure Search (like main.py does)
    raw_date = str(metadata.get("document_date", ""))
    if raw_date and raw_date.strip() not in ["", "None"]:
        if "T" not in raw_date:
            metadata["document_date"] = f"{raw_date.strip()}T00:00:00Z"
        else:
            metadata["document_date"] = raw_date.strip()
    else:
        metadata["document_date"] = None

    # Assign the Blob Name we generated earlier to the main index payload
    metadata["sharepoint_url"] = unique_blob_name

    # Build final document using the exact same builder as app.py
    mock_file = MockFile(filename)
    document = build_document(
        uploaded_file=mock_file,
        metadata=metadata,
        text=text,
        page_count=page_count,
        confidence=confidence,
        review_status="Completed" if is_valid else "Needs Review"
    )
    
    if not is_valid:
        print(f"[GMAIL-WORKER] Validation failed for {filename}. Routing to Action Centre.")
        
        reasons = []
        if validation_results["missing"]:
            reasons.append(f"Missing: {', '.join(validation_results['missing'])}")
        if validation_results["invalid"]:
            reasons.append(f"Invalid: {', '.join(validation_results['invalid'])}")
            
        metadata["file_name"] = filename
        metadata["status"] = "Needs Review"
        metadata["review_reason"] = f"Validation Failed - {' | '.join(reasons)}"
        add_review_document(metadata)
        log_document_status(
            file_name=filename, url="Gmail Ingestion", status="Needs Review",
            note=metadata["review_reason"], start_time=start_time, end_time=datetime.datetime.now(), word_count=len(text.split()) if text else 0
        )
    else:
        # Cross Validation against Policy Master Index
        doc_type = metadata.get("document_type", "").lower()
        if doc_type in ["major claim", "claim form", "claim closure", "claim closure report", "claim settlement"]:
            from src.validation.cross_validation_service import cross_validate_claim
            breach_errors = cross_validate_claim(metadata)
            
            if breach_errors:
                reason_str = " | ".join(breach_errors)
                print(f"[GMAIL-WORKER] Policy Breach for {filename}. Routing to Action Centre.")
                
                metadata["file_name"] = filename
                metadata["status"] = "Needs Review"
                metadata["review_reason"] = f"Policy Breach - {reason_str}"
                
                # Update the document payload status so it renders correctly if previewed
                document["status"] = "Needs Review"
                
                add_review_document(metadata)
                log_document_status(
                    file_name=filename, url="Gmail Ingestion", status="Needs Review",
                    note=f"Policy Breach. {reason_str}", start_time=start_time, end_time=datetime.datetime.now(), word_count=len(text.split()) if text else 0
                )
                return # Skip Azure Search upload
                
        print(f"[GMAIL-WORKER] Document is valid and passed all checks! Uploading to Azure AI Search...")
        upload_documents([document])
        log_document_status(
            file_name=filename, url="Gmail Ingestion", status="Completed",
            note="Indexed Automatically", start_time=start_time, end_time=datetime.datetime.now(), word_count=len(text.split()) if text else 0
        )
        
    # Log Document Hashes
    dedupe_service.log_document(file_bytes, document.get("id", ""), text, filename)

def start_ingestion_loop():
    agent = GmailAgent()
    dedupe_service = DuplicateDetectionService()
    
    print("========================================")
    print("   Automated Gmail Ingestion Started")
    print("========================================")
    
    if not agent.connect():
        print("Fatal Error: Could not connect to Gmail. Ensure credentials are correct in .env")
        return
        
    try:
        while True:
            try:
                # Ensure connection is alive before polling
                is_connected = False
                if agent.mail:
                    try:
                        agent.mail.noop()
                        is_connected = True
                    except Exception:
                        is_connected = False
                
                if not is_connected:
                    print(f"[GMAIL-WORKER] Connection dropped. Reconnecting...")
                    if not agent.connect():
                        print(f"[GMAIL-WORKER] Reconnection failed. Will retry in 60 seconds...")
                        time.sleep(60)
                        continue
                        
                print(f"\n[GMAIL-WORKER] [{datetime.datetime.now().strftime('%H:%M:%S')}] Polling for new emails...")
                emails = agent.fetch_unseen_emails()
                
                if not emails:
                    print("[GMAIL-WORKER] No new emails found.")
                
                for email_data in emails:
                    print(f"\n[GMAIL-WORKER] >>> Found Email: '{email_data['subject']}'")
                    
                    attachments = email_data.get("attachments", [])
                    if not attachments:
                        print("[GMAIL-WORKER] No valid attachments found. Skipping.")
                    
                    for attachment in attachments:
                        try:
                            process_email_attachment(email_data["body"], attachment, dedupe_service)
                        except Exception as e:
                            print(f"[GMAIL-WORKER] CRITICAL FAILURE processing {attachment.get('filename', 'Unknown')}: {e}")
                            # Ensure one bad attachment doesn't crash the background worker
                            continue
                        
                    # Mark as read after attempting to process all attachments
                    agent.mark_as_read(email_data["id"])
                    
            except Exception as loop_err:
                print(f"[GMAIL-WORKER] Error during IMAP poll: {loop_err}. Will retry in 60 seconds...")
                try:
                    agent.disconnect()
                except:
                    pass
                
            time.sleep(60) # Poll every 60 seconds
            
    except KeyboardInterrupt:
        print("\nStopping Ingestion Agent...")
        agent.disconnect()

if __name__ == "__main__":
    start_ingestion_loop()
