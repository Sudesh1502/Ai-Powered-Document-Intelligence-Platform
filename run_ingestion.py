import time
import uuid
import datetime
import os
from src.ingestion.gmail_agent import GmailAgent
from src.extraction.extraction_service import extract_text, calculate_confidence
from src.extraction.metadata_service import extract_metadata
from src.indexing.duplicate_detection_service import DuplicateDetectionService
from src.indexing.upload_document_service import upload_documents
from src.validation.validation_engine import validate_document_orchestrator, validate_email_intent_match
from src.utils.review_storage import add_review_document
from src.utils.document_builder import build_document
from src.utils.logger import log_document_status

class MockFile:
    def __init__(self, name):
        self.name = name

def process_email_attachment(email_body: str, attachment: dict, dedupe_service: DuplicateDetectionService):
    filename = attachment["filename"]
    file_bytes = attachment["data"]
    start_time = datetime.datetime.now()
    
    print(f"\n[+] Processing attachment: {filename}")
    
    # Layer 1: Exact Duplicate Detection
    if dedupe_service.is_exact_duplicate(file_bytes):
        print(f"[-] Exact duplicate detected for {filename}. Skipping.")
        return

    # Save file to disk temporarily for Azure OCR
    file_path = os.path.join("data", filename)
    os.makedirs("data", exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # Extract Text via OCR
    print(f"[*] Extracting text...")
    try:
        ocr_result = extract_text(file_path)
        text = ocr_result.content if ocr_result else ""
        confidence = calculate_confidence(ocr_result) if ocr_result else 0.0
        page_count = len(ocr_result.pages) if ocr_result and hasattr(ocr_result, "pages") else 1
    except Exception as e:
        print(f"[-] Azure OCR failed: {e}")
        text = ""
        confidence = 0.0
        page_count = 1
        
    if not text:
        print(f"[-] Failed to extract text from {filename}. Skipping.")
        return

    # Layer 2: Near-Duplicate Detection
    if dedupe_service.is_near_duplicate(text, file_bytes, filename):
        print(f"[-] Near duplicate detected for {filename}. Routing to Action Centre.")
        metadata_review = {
            "id": str(uuid.uuid4()),
            "file_name": filename,
            "document_title": filename,
            "status": "Needs Review",
            "review_reason": "Near-Duplicate (Text/Visual Similarity)"
        }
        add_review_document(metadata_review)
        return

    # Extract Metadata via Gemini
    print(f"[*] Extracting metadata via Gemini...")
    metadata = extract_metadata(text)
    
    # Layer 3: Data-Level Duplicate Detection
    if dedupe_service.is_data_level_duplicate(metadata):
        print(f"[-] Data-level duplicate detected for {filename}. Routing to Action Centre.")
        metadata["file_name"] = filename
        metadata["status"] = "Needs Review"
        metadata["review_reason"] = "Data-Level Duplicate (Matching ID & Vendor)"
        add_review_document(metadata)
        log_document_status(
            file_name=filename, url="Gmail Ingestion", status="Needs Review",
            note="Data-Level Duplicate (Matching ID & Vendor)", start_time=start_time, end_time=datetime.datetime.now(), word_count=len(text.split()) if text else 0
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
        print(f"[-] Validation failed for {filename}. Routing to Action Centre.")
        
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
        print(f"[+] Document is valid! Uploading to Azure AI Search...")
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
                print(f"\n[{datetime.datetime.now().strftime('%H:%M:%S')}] Polling for new emails...")
                emails = agent.fetch_unseen_emails()
                
                if not emails:
                    print("No new emails found.")
                
                for email_data in emails:
                    print(f"\n>>> Found Email: '{email_data['subject']}'")
                    
                    attachments = email_data.get("attachments", [])
                    if not attachments:
                        print("No valid attachments found. Skipping.")
                    
                    for attachment in attachments:
                        try:
                            process_email_attachment(email_data["body"], attachment, dedupe_service)
                        except Exception as e:
                            print(f"[-] CRITICAL FAILURE processing {attachment.get('filename', 'Unknown')}: {e}")
                            # Ensure one bad attachment doesn't crash the background worker
                            continue
                        
                    # Mark as read after attempting to process all attachments
                    agent.mark_as_read(email_data["id"])
                    
            except Exception as loop_err:
                print(f"[-] Error during IMAP poll: {loop_err}. Will retry in 60 seconds...")
                # Attempt to reconnect just in case connection dropped
                agent.connect()
                
            time.sleep(60) # Poll every 60 seconds
            
    except KeyboardInterrupt:
        print("\nStopping Ingestion Agent...")
        agent.disconnect()

if __name__ == "__main__":
    start_ingestion_loop()
