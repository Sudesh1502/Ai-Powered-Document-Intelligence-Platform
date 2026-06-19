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

        with open(
            QUEUE_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(
                f
            )

            if isinstance(
                data,
                list
            ):

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
    document_id
):

    documents = (
        load_review_documents()
    )

    documents = [

        d

        for d in documents

        if d.get(
            "id"
        )
        != document_id
    ]

    save_review_documents(
        documents
    )