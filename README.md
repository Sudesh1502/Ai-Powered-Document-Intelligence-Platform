
# AI-Powered Document Intelligence Platform

An end-to-end Intelligent Document Processing (IDP) platform designed to automate document ingestion, OCR extraction, metadata generation, validation, indexing, and intelligent search.

Built for processing large volumes of unstructured business documents, the platform leverages Azure Document Intelligence for OCR, Google Gemini for AI-powered metadata extraction, and Azure AI Search for fast semantic and keyword-based document retrieval.

The system supports both interactive document review through a Streamlit-based Action Centre and fully automated batch processing pipelines.

---

## Key Features

### Multi-Format Document Ingestion
- PDF documents
- Images (JPG, JPEG, PNG)
- Microsoft Word documents (DOCX)

### Intelligent OCR
- Powered by Azure Document Intelligence (`prebuilt-read`)
- Extracts text from scanned and digital documents
- Handles multi-page PDFs and image-based documents
- Captures OCR confidence scores

### AI-Powered Metadata Extraction

- Uses Google Gemini (`gemini-2.5-flash`)
- Generates structured JSON metadata from OCR text
- Extracts:
  - Document Type
  - Document Title
  - Document Number
  - Entity Name
  - Document Date
  - Page Count
  - Confidence Score
- Preserves full OCR content for search and retrieval
- Automatic retry mechanism using exponential backoff

### Validation Engine
Performs validation at multiple stages:

- File format validation
- File size validation
- Duplicate file detection(Ongoig)
- OCR confidence validation
- Metadata validation
- Date normalization
- Index record validation

###  Human-in-the-Loop Review (Action Centre)
The Streamlit-based Action Centre allows users to:

- Review AI-generated metadata
- Edit extracted fields
- Approve documents
- Reject documents
- Reprocess failed documents
- Monitor document status

### Intelligent Search
Supports:

- Keyword Search
- Semantic Search

### Azure AI Search Integration
- Automated document indexing
- Semantic ranking
- Fast retrieval
- Searchable knowledge base

### Automated Batch Processing
Process large document collections automatically using:

```bash
python main.py
```

### Comprehensive Logging
Tracks:

- Processing status
- OCR confidence
- Metadata extraction results
- Processing time
- Validation failures
- Search indexing status

---

## Architecture Pipeline

```text
Document Sources
(PDF / Images / DOCX)
          │
          ▼
Ingestion & Validation
          │
          ▼
Azure Document Intelligence
(OCR Extraction)
          │
          ▼
Google Gemini
(Metadata Generation)
          │
          ▼
Validation Engine
          │
          ▼
Action Centre Review
(Optional Human Approval)
          │
          ▼
Azure AI Search Index
          │
          ▼
Semantic & Keyword Search
```

---

## Technology Stack

| Component | Technology |
|------------|------------|
| Frontend UI | Streamlit |
| OCR Engine | Azure Document Intelligence |
| Generative AI | Google Gemini 2.5 Flash |
| Search Engine | Azure AI Search |
| Language | Python 3.10+ |
| Retry Mechanism | Tenacity |
| Configuration | Python Dotenv |
| Data Processing | Pandas |
| Storage | Local File System |

---

## Prerequisites

Before running the application, ensure you have:

- Python 3.12
- Azure Document Intelligence Resource
- Azure AI Search Service
- Google Gemini API Key
- Git

---

## Environment Configuration

Create a `.env` file in the root directory.

```env
# ==========================================
# Azure AI Search
# ==========================================

AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_API_ADMIN_KEY=your_admin_key
AZURE_SEARCH_API_QUERY_KEY=your_query_key
AZURE_SEARCH_INDEX_NAME=your_index_name

# ==========================================
# Azure Document Intelligence
# ==========================================

AZURE_OCR_ENDPOINT=https://your-ocr-service.cognitiveservices.azure.com
AZURE_OCR_API_KEY=your_ocr_key

# ==========================================
# Google Gemini
# ==========================================

GEMINI_API_KEY=your_gemini_api_key
```


---

#Installation

### 1. Clone the Repository

```bash
git clone https://adrosonic1@dev.azure.com/adrosonic1/DIL-Batch%202/_git/DIL-Batch%202

```

### 2. Create and Activate Virtual Environment

```bash
python -m venv .venv
```

#### Windows

```bash
.\.venv\Scripts\Activate
```

#### macOS / Linux

```bash
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

---

# How to Run

There are two ways to use the platform:

## 1. Run the UI (Streamlit)

Use the web-based interface to:

- Upload documents
- Review AI-generated metadata
- Manage pending reviews
- Search indexed documents

```bash
streamlit run app.py
```

---

## 2. Run the Background Batch Processor

Place your documents inside the data directory and process them automatically.

```bash
python main.py
```

---

# Supported File Formats

| Format |
|----------|
| PDF |
| JPG |
| JPEG  |
| PNG |
| DOCX  |

---

#  Search Examples

Search by:

### Customer Name

```text
John Smith
```

### Policy Number

```text
POL-2024-12345
```

### Claim ID

```text
CLM-987654
```

### Natural Language Queries

```text
Show all invoices above ₹50,000
```

```text
Find all documents related to policy POL-2024-12345
```

```text
Show documents submitted in June 2025
```

---

# Processing Workflow

1. Upload document
2. Validate file
3. OCR extraction using Azure Document Intelligence
4. Metadata generation using Gemini
5. Validation checks
6. Human review (optional)
7. Upload to Azure AI Search indexing
8. Search and retrieval

---

#  Logging

The platform maintains detailed logs for:

- OCR processing
- Metadata extraction
- Validation results
- Search indexing
- Processing failures
- Retry attempts

---
