ACORD_1_CRITICAL_FIELDS = {
    "document_type",
    "insured_name",
    "carrier_name",
    "policy_number",
    "date_of_loss",
    "property_location",
    "location_of_loss",
    "loss_type",
    "loss_description",
    "reported_by"
}

ACORD_24_CRITICAL_FIELDS = {
    "document_type",
    "certificate_date",
    "producer",
    "insured_name",
    "company_name",
    "policy_number",
    "policy_effective_date",
    "policy_expiration_date",
    "insurance_type",
    "certificate_holder",
    "authorized_representative"
}

ACORD_36_CRITICAL_FIELDS = {
    "document_type",
    "named_insured",
    "insurance_company_name",
    "new_agency",
    "effective_date",
    "line_of_business",
    "insured_signature",
    "signature_date"
}

CLAIM_CLOSURE_CRITICAL_FIELDS = {
    "document_type",
    "claim_number",
    "policy_number",
    "insured_name",
    "date_of_loss",
    "date_of_closure",
    "settlement_amount",
    "claim_status"
}