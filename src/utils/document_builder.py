import uuid
import json


def build_document(
        uploaded_file,
        metadata,
        text,
        page_count,
        confidence,
        review_status
):

    return {

        "id":
            str(
                uuid.uuid4()
            ),

        "file_name":
            uploaded_file.name,

        "document_type":
            metadata.get(
                "document_type"
            ),

        "document_title":
            metadata.get(
                "document_title"
            ),

        "content":
            text,

        "document_number":
            metadata.get(
                "document_number"
            ),

        "entity_name":
            metadata.get(
                "entity_name"
            ),

        "amount":
            metadata.get(
                "amount"
            ),

        "document_date":
            metadata.get(
                "document_date"
            ),

        "page_count":
            page_count,

        "confidence":
            confidence,

        "metadata":
            json.dumps(
                metadata
            ),

        "sharepoint_url":
            ""
    }