import json
import markdown2
from xhtml2pdf import pisa
from io import BytesIO
from google import genai
from src.config.config import GEMINI_API_KEY

def generate_investigation_report(search_results: list, user_query: str) -> str:
    """
    Generates a comprehensive investigation report using Gemini.
    """
    print(f"\nGenerating investigation report for: '{user_query}'...")
    
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # Clean the search results so the LLM doesn't get confused by UUIDs or URLs
    clean_results = []
    for doc in search_results:
        clean_doc = doc.copy()
        clean_doc.pop("id", None)
        clean_doc.pop("rank", None)
        clean_doc.pop("score", None)
        clean_doc.pop("sharepoint_url", None) # Often contains UUIDs
        clean_results.append(clean_doc)
        
    # Format the search results as a pretty JSON string
    docs_json = json.dumps(clean_results, indent=2)
    
    prompt = f"""You are an insurance investigation assistant.

Your task is to generate a comprehensive investigation report using ONLY the retrieved documents.

SEARCH ENTITY
{user_query}

DOCUMENTS
{docs_json}

Instructions

1. You MUST use the EXACT Markdown template provided below. Do not change the heading levels, add new headings, or deviate from this structure.
2. Combine information from all documents and remove duplicates.
3. If information is unavailable for a section, explicitly state: "Information not found in the available documents."
4. Do not invent facts.

CRITICAL CITATION RULES: 
For every statement, reference the document(s) it came from. You MUST use the exact `file_name` field for all document references (e.g., 'Sample Invoice.pdf'). DO NOT use long alphanumeric codes, UUIDs, or IDs anywhere in the report.

### REQUIRED MARKDOWN TEMPLATE:

## Investigation Report: {user_query}

**Date:** [Current Date]
**Investigation Assistant:** AI Assistant
**Search Entity:** {user_query}

### Executive Summary
[Provide a concise 2-3 sentence summary of the findings, citing document names]

### Entity & Claim Overview
*   **Entity Name:** [Name] ([file_name])
*   **Policy Number:** [Number] ([file_name])
*   **Claim Number:** [Number] ([file_name])
*   **Date of Loss:** [Date] ([file_name])

### Timeline of Events
*   **[Date/Time]:** [Event description] ([file_name])
*   **[Date/Time]:** [Event description] ([file_name])

### Key Findings & Observations
[Provide detailed findings, financial information, and cross-document observations here, strictly citing file names]

### Missing Information & Discrepancies
[Note any missing critical information or conflicting data between documents]

### AI Recommendations
[Provide next steps for the claims handler based on the findings]

    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=prompt
        )

        if not response.text:
            return "Error: Empty response from Gemini."

        print("Investigation report generated successfully.")
        print(response.text.strip())
        return response.text.strip()

    except Exception as e:
        print(f"Report generation failed: {e}")
        return f"Error generating report: {str(e)}"

def generate_pdf_from_markdown(markdown_text: str) -> bytes:
    """
    Converts a markdown string to a PDF byte-stream using markdown2 and xhtml2pdf.
    """
    # Convert markdown to HTML (handling tables and basic extensions)
    html_content = markdown2.markdown(markdown_text, extras=["tables", "fenced-code-blocks", "cuddled-lists"])
    
    # Basic CSS injection to make the PDF look professional and structured
    styled_html = f"""
    <html>
    <head>
        <style>
            @page {{
                size: a4 portrait;
                margin: 2cm;
            }}
            body {{
                font-family: Helvetica, Arial, sans-serif;
                font-size: 11pt;
                line-height: 1.5;
                color: #333333;
            }}
            b, strong {{
                font-weight: bold;
            }}
            h1 {{
                color: #2c3e50;
                font-size: 24pt;
                border-bottom: 2px solid #3498db;
                padding-bottom: 5px;
                margin-bottom: 20px;
            }}
            h2 {{
                color: #2980b9;
                font-size: 18pt;
                margin-top: 25px;
                margin-bottom: 10px;
            }}
            h3 {{
                color: #34495e;
                font-size: 14pt;
                margin-top: 15px;
            }}
            p {{
                margin-bottom: 10px;
                text-align: justify;
            }}
            ul {{
                margin-bottom: 10px;
            }}
            li {{
                margin-bottom: 4px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
                margin-bottom: 15px;
            }}
            th, td {{
                border: 1px solid #bdc3c7;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #ecf0f1;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Generate the PDF byte stream
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(styled_html.encode("UTF-8")), result)
    
    if not pdf.err:
        return result.getvalue()
    else:
        raise Exception(f"Failed to generate PDF: {pdf.err}")
