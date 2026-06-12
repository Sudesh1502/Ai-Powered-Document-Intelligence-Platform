"""
This file handles the ingestion and validation of raw documents.
"""
from pathlib import Path
from pypdf import PdfReader

MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_PDF_PAGES = 20

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".jpg",
    ".jpeg",
    ".png"
}

BLOCKED_EXTENSIONS = {
    ".zip",
    ".rar",
    ".7z",
    ".tar",
    ".gz"
}


def validate_pdf(file_path: Path) -> tuple[bool, str]:
    """Validates a PDF file for encryption and page limits."""
   
    try:
        reader = PdfReader(str(file_path))

        if reader.is_encrypted:
            return False, "Password-protected PDF"

        page_count = len(reader.pages)

        if page_count > MAX_PDF_PAGES:
            return False, f"PDF has {page_count} pages (limit: {MAX_PDF_PAGES})"

        return True, ""

    except Exception as e:
        return False, f"Invalid PDF: {e}"


def get_unprocessed_documents(raw_dir: str):
    """Retrieves and validates unprocessed documents from a directory."""
   
    raw_path = Path(raw_dir)

    if not raw_path.exists():
        raw_path.mkdir(parents=True, exist_ok=True)
        print(f"Created raw data directory: {raw_dir}")
        return []

    documents = []

    for file in raw_path.iterdir():

        try:
            # Skip directories
            if not file.is_file():
                continue

            extension = file.suffix.lower()

            # Reject archives
            if extension in BLOCKED_EXTENSIONS:
                print(f"Skipped {file.name}: Archive files are not allowed")
                continue

            # Allow only supported types
            if extension not in SUPPORTED_EXTENSIONS:
                print(f"Skipped {file.name}: Unsupported file type")
                continue

            # File size validation
            file_size = file.stat().st_size

            if file_size > MAX_FILE_SIZE_BYTES:
                print(
                    f"Skipped {file.name}: "
                    f"File size exceeds {MAX_FILE_SIZE_MB} MB"
                )
                continue

            # PDF-specific validation
            if extension == ".pdf":
                is_valid, reason = validate_pdf(file)

                if not is_valid:
                    print(f"Skipped {file.name}: {reason}")
                    continue

            documents.append(str(file.resolve()))

        except Exception as e:
            print(f"Error processing {file.name}: {e}")

    return documents