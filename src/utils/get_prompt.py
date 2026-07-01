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
    "document_date": null,
    "metadata": {{}}
}}

Field Definitions:

document_type:
- MUST be exactly one of the following values:
  - acord form
  - claim closure report
  - major claim
  - aadhar
  - claim settlement
  - incident image
  - invoice
  - other
- If the document does not explicitly match one of the specific types above, you MUST return "other".

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

aadhaar_number:
- The 12-digit unique Aadhaar identity number (e.g., 4587 2468 1357)

dob:
- Date of Birth (e.g., 15/07/1990 or 1990-07-15)

entity_name:
- MUST be the primary individual or customer the document is about (e.g., the Insured Person, Claimant, or Customer).
- NEVER use the name of the Insurance Company, Carrier, Agency, or Broker as the entity_name.
- examples:
  - customer
  - insured person
  - claimant
  - patient



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

Conditional Metadata Requirements:
Depending on the document, you MUST include the following exact keys inside the 'metadata' JSON object. If the information is not found in the text, assign the value as "N/A".
- If document_type is "acord form" and title is "Property Loss Notice", you MUST extract exactly these keys: {list(ACORD_1_CRITICAL_FIELDS)}
- If document_type is "acord form" and title is "Certification of property insurance", you MUST extract exactly these keys: {list(ACORD_24_CRITICAL_FIELDS)}
- If document_type is "acord form" and title is "Agent/Broker of Record Change", you MUST extract exactly these keys: {list(ACORD_36_CRITICAL_FIELDS)}
- If document_type is "claim closure report", you MUST extract exactly these keys: {list(CLAIM_CLOSURE_CRITICAL_FIELDS)}
- If document_type is "claim settlement", you MUST extract exactly these keys: {list(CLAIM_SETTLEMENT_CRITICAL_FIELDS)}
- If document_type is "aadhar", you MUST extract exactly these keys: {list(AADHAAR_CRITICAL_FIELDS)}
- If the document is a Major Claim Document, you MUST extract exactly these keys: {list(MAJOR_CLAIM_CRITICAL_FIELDS)}
- If document_type is "incident image", you MUST generate and extract exactly these keys based on your visual analysis of the damage: {list(INCIDENT_IMAGE_CRITICAL_FIELDS)}
- If document_type is "invoice", you MUST extract exactly these keys: {list(INVOICE_CRITICAL_FIELDS)}

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
- If the document contains multiple languages (e.g., Aadhaar cards with Hindi and English), you MUST extract the English version of the names and text.
- If ANY critical field or metadata value is missing or not explicitly found in the document text, you MUST assign it as "N/A" or null. Do not leave it blank.
- Return ONLY valid JSON.
- Do not wrap the response in markdown.
- Do not include explanations.

DOCUMENT:

{text}
"""

def get_search_summary_prompt(
    user_query: str,
    search_type: str,
    search_results: list
):
    return f"""
You are an intelligent enterprise search assistant.
 
Your goal is to help the user understand how the returned documents relate to their search query.
 
SEARCH QUERY:
{user_query}

SEARCH TYPE:
{search_type}
Possible values:
- keyword
- semantic
 
SEARCH RESULTS:
{search_results}
 
INSTRUCTIONS:
 
1. First understand what the user is looking for.
 
2. Review all returned search results and determine which documents appear most relevant to the user's query.
 
3. Write a user-facing summary that explains:
   - which documents best match the user's request,
   - what information was found,
   - which documents may be partially relevant,
   - and any important details the user should know.
 
4. Speak directly to the user:
   - Use phrases such as:
     - "Based on your search..."
     - "The strongest match appears to be..."
     - "These documents may also be relevant..."
     - "No document explicitly states..."
 
5. Do NOT explain search algorithms, scoring, rankings, embeddings, semantic search, keywords, or retrieval mechanics.
 
6. Do NOT simply list documents one by one unless necessary.
 
7. Synthesize findings into a natural search response that helps the user quickly understand the results.
 
8. If no strong match exists, clearly state that the retrieved documents do not contain a direct answer.
 
9. Never invent information.
 
10. Keep the response concise, user-focused, and actionable.
 
11. Maximum length: 500 words.
"""