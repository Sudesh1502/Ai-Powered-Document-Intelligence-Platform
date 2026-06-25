# Import the sets you created
from src.validation.document_validation_fields import (
    ACORD_1_CRITICAL_FIELDS,
    ACORD_24_CRITICAL_FIELDS,
    ACORD_36_CRITICAL_FIELDS,
    CLAIM_CLOSURE_CRITICAL_FIELDS
)

def validate_claim_closure(metadata: dict) -> list:
    """
    Validates a Claim Closure Report. Returns a list of missing fields.
    """
    missing_fields = []
    
    for field in CLAIM_CLOSURE_CRITICAL_FIELDS:
        value = metadata.get(field)
        
        if value is None and "metadata" in metadata and isinstance(metadata["metadata"], dict):
            value = metadata["metadata"].get(field)
            
        if not value or str(value).strip() == "" or str(value).strip().lower() in ["n/a", "not found", "null", "none", "-", "not specified", "unknown"]:
            missing_fields.append(field)
            
    return missing_fields

def validate_acord_form(metadata: dict) -> list:
    """
    Validates an ACORD form. Returns a list of missing fields.
    """
    doc_title = metadata.get("document_title", "").lower()
    critical_fields = set()
    
    # Strictly map based on title
    if "property loss notice" in doc_title:
        critical_fields = ACORD_1_CRITICAL_FIELDS
    elif "certification of property insurance" in doc_title or "certificate of property insurance" in doc_title:
        critical_fields = ACORD_24_CRITICAL_FIELDS
    elif "agent/broker of record change" in doc_title or "agent or broker of record change" in doc_title:
        critical_fields = ACORD_36_CRITICAL_FIELDS
    else:
        # If it's an ACORD form but the title doesn't match our 3 supported ones, 
        # we can't validate it, so it passes.
        return []
        
    missing_fields = []
    
    # Loop through the specific set and validate
    for field in critical_fields:
        # First, check if the field is at the top level of the JSON (like document_type)
        value = metadata.get(field)
        
        # If it's not at the top level, look inside the nested "metadata" dictionary!
        if value is None and "metadata" in metadata and isinstance(metadata["metadata"], dict):
            value = metadata["metadata"].get(field)
            
        # Now validate the value
        if not value or str(value).strip() == "" or str(value).strip().lower() in ["n/a", "not found", "null", "none", "-", "not specified", "unknown"]:
            missing_fields.append(field)
            
    return missing_fields


def validate_document_orchestrator(metadata: dict) -> list:
    """
    The main routing hub for all document validations.
    """
    doc_type = metadata.get("document_type", "").lower()
    
    doc_title = metadata.get("document_title", "").lower()
    
    # Route to ACORD validation
    if "acord" in doc_type or "accord" in doc_type:
        return validate_acord_form(metadata)
    
    # Route to Claim Closure validation
    elif "claim closure" in doc_type or "closure" in doc_title:
        return validate_claim_closure(metadata)
        
    # Route to Invoice validation
    elif "invoice" in doc_type:
        # return validate_invoice(metadata)
        pass
        
    # If we don't have a specific validator for this type yet, let it pass
    return []