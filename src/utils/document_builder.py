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
            metadata.get("sharepoint_url", "")
    }

def build_policy_document(
        uploaded_file,
        metadata
):
    import uuid

    # Helper function to format dates correctly for Azure Search (Edm.DateTimeOffset)
    def format_date(date_str):
        if not date_str or str(date_str).strip().lower() in ["n/a", "null", "none", ""]:
            return None
        date_str = str(date_str).strip()
        if "T" not in date_str:
            return f"{date_str}T00:00:00Z"
        return date_str

    return {
        "id": str(uuid.uuid4()),
        "policy_number": str(metadata.get("policy_number", "N/A")),
        "insured_name": str(metadata.get("insured_name", "N/A")),
        "class_of_business": str(metadata.get("class_of_business", "N/A")),
        "policy_effective_date": format_date(metadata.get("policy_effective_date")),
        "policy_expiration_date": format_date(metadata.get("policy_expiration_date")),
        "risk_locations": metadata.get("risk_locations") if isinstance(metadata.get("risk_locations"), list) else [],
        "policy_limit": float(metadata.get("policy_limit") or 0.0),
        "sub_limits": metadata.get("sub_limits") if isinstance(metadata.get("sub_limits"), list) else [],
        "deductible_excess": float(metadata.get("deductible_excess") or 0.0),
        "relevant_clauses": metadata.get("relevant_clauses") if isinstance(metadata.get("relevant_clauses"), list) else [],
        "exclusions": metadata.get("exclusions") if isinstance(metadata.get("exclusions"), list) else [],
        "notification_conditions": str(metadata.get("notification_conditions", "N/A")),
        "file_name": uploaded_file.name,
        "sharepoint_url": metadata.get("sharepoint_url", "")
    }