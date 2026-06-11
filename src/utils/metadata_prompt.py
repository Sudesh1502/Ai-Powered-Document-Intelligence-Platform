def get_metadata_extraction_prompt(text: str) -> str:
    return f"""
You are an expert document understanding system.

Analyze the document and extract structured metadata.

Return ONLY valid JSON.

Schema:

{{
    "document_type": "",
    "document_title": "",
    "document_number": "",
    "entity_name": "",
    "amount": null,
    "document_date": null,
    "metadata": {{}}
}}

Field Definitions:

document_type:
- invoice
- claim
- contract
- report
- receipt
- application
- policy
- notice
- correspondence
- other

document_title:
- the title or heading of the document
- examples:
  - "Invoice for Services Rendered"
  - "Annual Maintenance Contract"
  - "Water Damage Claim Form"

document_number:
- primary identifier for the document
- examples:
  - invoice number
  - claim number
  - policy number
  - contract number
  - reference number

entity_name:
- primary business entity associated with the document
- examples:
  - customer
  - insured person
  - vendor
  - claimant
  - company
  - organization

amount:
- primary monetary value in the document
- return as a number
- do not include currency symbols
- if not available return null

document_date:
- most important business date in the document
- return in ISO format: YYYY-MM-DD
- if unavailable return null

metadata:
- include all additional business-relevant information
- use snake_case keys
- examples:
  {{
      "policy_number": "",
      "carrier_name": "",
      "loss_type": "",
      "vendor_name": "",
      "contact_name": ""
  }}

Rules:

- Fix obvious OCR mistakes when possible.
- Use snake_case for metadata keys.
- Ignore page numbers.
- Ignore footer text.
- Ignore headers repeated on every page.
- Ignore legal notices.
- Ignore fraud warnings.
- Ignore disclaimers.
- Ignore copyright notices.
- Ignore instructions and boilerplate text.
- Do not hallucinate values.
- If a field is not present, return null.
- Return ONLY valid JSON.
- Do not wrap the response in markdown.
- Do not include explanations.

DOCUMENT:

{text}
"""