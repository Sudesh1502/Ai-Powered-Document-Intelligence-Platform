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
You are an enterprise document search assistant.

Your task is to generate a concise search summary for the user based ONLY on the provided search results.

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

1. Analyze the metadata, captions, and content of all returned documents.
2. Generate a professional, cohesive summary of the ACTUAL INFORMATION contained within these documents.
3. Synthesize the key facts, figures, dates, entity names, and narratives found in the search results.
4. Do NOT explain why the documents were returned. Do NOT discuss search algorithms, keyword overlap, or ranking mechanics.
5. Focus purely on answering the user's implicit question by extracting the most relevant data from the results.
6. If the documents contain financial amounts, dates, or specific claim details, ensure you highlight them in your summary.
7. If no relevant information can be extracted from the documents to satisfy the query, politely state that the retrieved documents do not contain a direct answer.

8. Never invent information.
9. Never mention internal system details, vector embeddings, LLMs, Azure implementation details, or confidence estimates unless explicitly provided.
10. Maximum length: 500 words.
11. Use a professional business-report style.

IMPORTANT:

- Do not assume a document discusses a topic unless the title,
  metadata, or semantic caption explicitly indicates it.
- If evidence is insufficient, state that relevance is inferred
  from available metadata.
- Never claim that a document contains information that is not
  present in the provided search results.

Provide a highly direct, concise summary of the core facts found in the documents. You may use bullet points to list the findings cleanly, but DO NOT use any headings (like "Summary:", "Key Findings:", or "Relevance Assessment:"). Ensure there is absolutely no repetitive phrasing.

Examples:

Example 1:
User Query:
"I want all documents that claim insurance for water damage"

Expected Style:
The search returned 5 property loss notices:
* One document (dated May 22, 2024 for Michael James Anderson) explicitly lists a flood claim with an estimated amount of $15,000.
* The remaining four documents detail other claim submissions involving Liberty Mutual and Harbor Insurance Group, but do not specifically reference water damage.

Return plain text only.
Do not use markdown code blocks.

Generate the summary now.
"""