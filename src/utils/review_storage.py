import json
import os


QUEUE_FILE = (
    "app_data/review_queue.json"
)


def load_review_documents():

    if not os.path.exists(
        QUEUE_FILE
    ):

        return []

    try:

        with open(QUEUE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                # Inject IDs for backwards compatibility with old queue items
                import uuid
                modified = False
                for d in data:
                    if "id" not in d:
                        d["id"] = d.get("file_name", str(uuid.uuid4()))
                        modified = True
                
                # If we had to fix old data, save it immediately
                if modified:
                    with open(QUEUE_FILE, "w", encoding="utf-8") as out_f:
                        json.dump(data, out_f, indent=4, ensure_ascii=False, default=str)
                        
                return data
            return []

    except Exception:

        return []


def save_review_documents(
    documents
):

    with open(
        QUEUE_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            documents,
            f,
            indent=4,
            ensure_ascii=False,
            default=str
        )


def add_review_document(
    document
):
    import uuid
    if "id" not in document:
        document["id"] = str(uuid.uuid4())

    documents = (
        load_review_documents()
    )

    documents.append(
        document
    )

    save_review_documents(
        documents
    )


def remove_review_document(
    document_id_or_name
):

    documents = (
        load_review_documents()
    )

    documents = [
        d
        for d in documents
        if d.get("id") != document_id_or_name and d.get("file_name") != document_id_or_name
    ]

    save_review_documents(
        documents
    )