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

1. Analyze all returned documents.
2. Determine whether the results contain:
   - Strong/exact matches to the user's intent.
   - Partial matches.
   - Only related documents.

3. Generate a professional search summary in natural language.

4. Explain:
   - How many documents were returned.
   - Whether the documents directly satisfy the query.
   - Why the documents were ranked highly.
   - Which important keywords, entities, captions, titles, or metadata contributed to the ranking.

5. If SEARCH TYPE is "semantic":
   - Use semantic captions when available.
   - Mention that ranking considered semantic meaning and contextual relevance.

6. If SEARCH TYPE is "keyword":
   - Mention that ranking was based primarily on keyword overlap and relevance scoring.

7. If no strong matches exist:
   - Clearly state that no exact matches were found.
   - Explain that related documents were returned instead.
   - Describe what similarities caused them to be retrieved.

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

OUTPUT FORMAT:

Summary:
<summary paragraph>

Key Findings:
- finding 1
- finding 2
- finding 3

Relevance Assessment:
<one sentence explaining whether results are exact, partial, or related matches>

Examples:

Example 1:
User Query:
"I want all documents that claim insurance for water damage"

Expected Style:
"Found 7 documents relevant to insurance claims involving water damage. Most highly ranked documents contain references to water-related incidents, claim submissions, damage assessments, and insurance processing details. Documents were ranked based on the strength of their relevance to the requested claim scenario and the presence of supporting claim-related information."

Example 2:
If no exact matches:
"No documents explicitly describing insurance claims for water damage were found. However, 5 related documents were retrieved because they contain references to insurance claims, property damage, incident reports, or claim assessment activities that may be relevant to the request."

Return plain text only.
Do not use markdown code blocks.

Generate the summary now.
"""