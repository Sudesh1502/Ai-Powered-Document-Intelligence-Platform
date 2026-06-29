# Import the sets you created
from src.validation.document_validation_fields import (
    ACORD_1_CRITICAL_FIELDS,
    ACORD_24_CRITICAL_FIELDS,
    ACORD_36_CRITICAL_FIELDS,
    CLAIM_CLOSURE_CRITICAL_FIELDS,
    MAJOR_CLAIM_CRITICAL_FIELDS,
    AADHAAR_CRITICAL_FIELDS,
    CLAIM_SETTLEMENT_CRITICAL_FIELDS,
    INCIDENT_IMAGE_CRITICAL_FIELDS,
    INVOICE_CRITICAL_FIELDS
)

def validate_claim_closure(metadata: dict) -> dict:
    """
    Validates a Claim Closure Report. Returns a dictionary of missing and invalid fields.
    """
    return _validate_fields(metadata, CLAIM_CLOSURE_CRITICAL_FIELDS)

def validate_acord_form(metadata: dict) -> dict:
    """
    Validates an ACORD form. Returns a dictionary of missing and invalid fields.
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
        return {"missing": [], "invalid": []}
        
    return _validate_fields(metadata, critical_fields)


import re

# Dictionary of strict formatting rules
FORMAT_RULES = {
    "aadhaar_number": r"^\d{4}\s?\d{4}\s?\d{4}$", # Exactly 12 digits, optional spaces
    "insured_name": r"^[^\d_]+$", # Allow any language, strictly block numbers
    "claimant_name": r"^[^\d_]+$",
    "vendor_name": r"^[^\d_]+$",
    "name": r"^[^\d_]+$",
    "settlement_amount": r"^[\d,\.]+$", # Numeric amounts, multiple commas and decimals allowed
    "total_due": r"^[\d,\.]+$",
    "paid_amount_100": r"^[\d,\.]+$",
    "date_of_loss": r"^\d{1,4}[-/\.\s][a-zA-Z0-9]+[-/\.\s]\d{1,4}$", # Matches YYYY-MM-DD, MM/DD/YYYY, 15 May 2026
    "date_of_closure": r"^\d{1,4}[-/\.\s][a-zA-Z0-9]+[-/\.\s]\d{1,4}$",
    "certificate_date": r"^\d{1,4}[-/\.\s][a-zA-Z0-9]+[-/\.\s]\d{1,4}$",
    "policy_effective_date": r"^\d{1,4}[-/\.\s][a-zA-Z0-9]+[-/\.\s]\d{1,4}$",
    "policy_expiration_date": r"^\d{1,4}[-/\.\s][a-zA-Z0-9]+[-/\.\s]\d{1,4}$",
    "effective_date": r"^\d{1,4}[-/\.\s][a-zA-Z0-9]+[-/\.\s]\d{1,4}$",
    "signature_date": r"^\d{1,4}[-/\.\s][a-zA-Z0-9]+[-/\.\s]\d{1,4}$",
    "loss_date_from": r"^\d{1,4}[-/\.\s][a-zA-Z0-9]+[-/\.\s]\d{1,4}$",
    "dob": r"^\d{1,4}[-/\.\s][a-zA-Z0-9]+[-/\.\s]\d{1,4}$",
    "letter_date": r"^\d{1,4}[-/\.\s][a-zA-Z0-9]+[-/\.\s]\d{1,4}$",
    "invoice_date": r"^\d{1,4}[-/\.\s][a-zA-Z0-9]+[-/\.\s]\d{1,4}$"
}

def _validate_fields(metadata: dict, fields_set: set) -> dict:
    missing_fields = []
    invalid_fields = []
    
    for field in fields_set:
        value = metadata.get(field)
        if value is None and "metadata" in metadata and isinstance(metadata["metadata"], dict):
            value = metadata["metadata"].get(field)
            
        # 1. Check if missing
        if not value or str(value).strip() == "" or str(value).strip().lower() in ["n/a", "not found", "null", "none", "-", "not specified", "unknown"]:
            missing_fields.append(field)
        else:
            # 2. If present, check if it fails format validation
            if field in FORMAT_RULES:
                # Remove currency symbols for amount validation just in case
                test_value = str(value).replace("$", "").replace("€", "").replace("£", "").replace("₹", "").strip()
                if not re.match(FORMAT_RULES[field], test_value):
                    invalid_fields.append(f"{field} ('{value}')")
                    
    return {"missing": missing_fields, "invalid": invalid_fields}



def validate_major_claim(metadata: dict) -> dict:
    return _validate_fields(metadata, MAJOR_CLAIM_CRITICAL_FIELDS)

def validate_aadhaar(metadata: dict) -> dict:
    return _validate_fields(metadata, AADHAAR_CRITICAL_FIELDS)

def validate_claim_settlement(metadata: dict) -> dict:
    return _validate_fields(metadata, CLAIM_SETTLEMENT_CRITICAL_FIELDS)

def validate_incident_image(metadata: dict) -> dict:
    return _validate_fields(metadata, INCIDENT_IMAGE_CRITICAL_FIELDS)

def validate_invoice(metadata: dict) -> dict:
    return _validate_fields(metadata, INVOICE_CRITICAL_FIELDS)


def validate_document_orchestrator(metadata: dict) -> dict:
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

    # Route to Major Claim validation
    elif "major claim" in doc_type or "major claim" in doc_title:
        return validate_major_claim(metadata)
        
    # Route to Aadhaar validation
    elif "aadhar" in doc_type or "aadhaar" in doc_type or "adhar" in doc_title:
        return validate_aadhaar(metadata)
        
    # Route to Claim Settlement validation
    elif "settlement" in doc_type or "settlement" in doc_title:
        return validate_claim_settlement(metadata)

    # Route to Incident Image validation
    elif "incident image" in doc_type or "image" in doc_type:
        return validate_incident_image(metadata)
        
    # Route to Invoice validation
    elif "invoice" in doc_type:
        return validate_invoice(metadata)
        
    # If we don't have a specific validator for this type yet, let it pass
    return {"missing": [], "invalid": []}