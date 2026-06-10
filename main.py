
# documents = [
#     {
#         "id": "1",
#         "file_name": "invoice_001.pdf",
#         "content": "White Forest Cake 1kg amount 1000",
#         "document_type": "invoice",
#         "amount": 1000,
#         "date": "2026-03-31T00:00:00Z",
#         "sharepoint_url": "https://sharepoint.com/invoice1"
#     },
#     {
#         "id": "2",
#         "file_name": "claim_001.pdf",
#         "content": "Water damage insurance claim amount 5000",
#         "document_type": "claim",
#         "amount": 5000,
#         "date": "2026-04-01T00:00:00Z",
#         "sharepoint_url": "https://sharepoint.com/claim1"git
#     }
# ]
import uuid
from pathlib import Path
from src.ingestion.ingestion_service import get_unprocessed_documents
from src.extraction.extraction_service import calculate_confidence
from src.extraction.extraction_service import extract_text
from src.extraction.metadata_service import extract_metadata
from src.indexing.indexing_service import create_index
from src.indexing.upload_document_service import upload_documents
import json

BASE_DIR = Path(__file__).resolve().parent
RAW_DATA_DIR = BASE_DIR / "data"

documents = get_unprocessed_documents(RAW_DATA_DIR)

if not documents:
    print("\nDirectory is empty")


print("\nprocessing documents for extraction")
print(f"\nToatl {len(documents)} found.")

doc = documents[0]




result = extract_text(doc)
confidence = calculate_confidence(result)
metadata = extract_metadata(
    result.content
)
if "error" in metadata:
    print(
        f"Metadata extraction failed: "
        f"{metadata['error']}"
    )
    exit()

indexed_document = {
    "id": str(uuid.uuid4()),

    "file_name": Path(doc).name,

    "document_type": metadata.get("document_type"),

    "content": result.content,

    "document_number": metadata.get("document_number"),

    "entity_name": metadata.get("entity_name"),

    "amount": metadata.get("amount"),

    "document_date": metadata.get("document_date"),

    "page_count": len(result.pages),

    "confidence": confidence,

    "metadata": json.dumps(
        metadata.get("metadata", {})
    ),

    "sharepoint_url": ""
}

print("\nThis is the index created.")
print(
    json.dumps(
        indexed_document,
        indent=4,
        ensure_ascii=False
    )
)

upload_result = upload_documents([indexed_document])


print(upload_result)




# for doc in documents:
#     doc = Path(doc)
#     print(f"\n\nProcessing file {doc.name}")
    
    
#     result = extract_text(doc)
    
#     confidence = calculate_confidence(result)
    
    
#     print(f"Confidence of file {doc.name} if {confidence}")




# index = create_index()

# print(index)