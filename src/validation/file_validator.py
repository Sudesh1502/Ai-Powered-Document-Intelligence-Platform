from pathlib import Path


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".docx"
}


def is_valid_file(file_path):

    extension = Path(file_path).suffix.lower()

    return extension in ALLOWED_EXTENSIONS