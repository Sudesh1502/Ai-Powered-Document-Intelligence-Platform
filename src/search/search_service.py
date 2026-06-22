from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import QueryType, QueryCaptionType
from src.utils.get_prompt import get_search_summary_prompt

from src.config.config import (
    AZURE_SEARCH_ENDPOINT,
    AZURE_SEARCH_ADMIN_KEY
)
from google import genai

from src.config.config import GEMINI_API_KEY

def get_summary(search_results:list, user_query:str, semantic_search:bool):
    print("\nSummary extraction started...")
    client = genai.Client(
        api_key=GEMINI_API_KEY
    )
    search_type = "semantic" if semantic_search else "keyword"
    summary_prompt = get_search_summary_prompt(user_query, search_type, search_results)

    try:

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=summary_prompt
        )

        if not response.text:
            return {
                "error": "Empty response from Gemini"
            }

        output = response.text.strip()

        

        summary = output

        print("\nSummary extraction completed...")

        return summary

    except Exception as e:

        return {
            "error": str(e)
        }
    

def search_documents(
    query: str, 
    use_semantic_ranker: bool = False, 
    filters: str = None, 
    top: int = 10
):
    """
    Executes a search query against the Azure AI Search index.
    
    :param query: The search text to look for.
    :param use_semantic_ranker: If True, uses the semantic ranker for better relevance and captions.
    :param filters: OData filter string (e.g., "document_type eq 'invoice'").
    :param top: Number of results to return.
    """
    print(f"\nExecuting search for: '{query}' (Semantic: {use_semantic_ranker})")
    
    # Initialize the search client
    search_client = SearchClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        index_name="generic-documents-index",
        credential=AzureKeyCredential(AZURE_SEARCH_ADMIN_KEY)
    )

    # Base search parameters to optimize the network payload
    search_kwargs = {
        "search_text": query,
        "filter": filters,
        "top": top,
        "select": [
            "id", "file_name", "document_title", "document_type", 
            "entity_name", "document_date", "confidence", "sharepoint_url"
        ]
    }

    # Add semantic parameters if requested
    if use_semantic_ranker:
        search_kwargs.update({
            "query_type": "semantic",
            "semantic_configuration_name": "default-semantic-config",
            "query_caption": "extractive"
        })

    try:
        # Execute the search request
        results = search_client.search(**search_kwargs)
        
        formatted_results = []
        for rank, result in enumerate(results, start=1):
            doc_data = {
                "rank": rank,
                "id": result["id"],
                "file_name": result.get("file_name"),
                "document_title": result.get("document_title"),
                "document_type": result.get("document_type"),
                "document_date": result.get("document_date"),
                "entity_name": result.get("entity_name"),
                "sharepoint_url": result.get("sharepoint_url"),
                "score": round(result["@search.score"], 3)
            }
            
            # If semantic search is used, Azure provides exact text snippets (captions) where it found the answer
            if use_semantic_ranker and result.get("@search.captions"):
                captions = [c.text for c in result["@search.captions"]]
                doc_data["semantic_captions"] = captions
                
            formatted_results.append(doc_data)
            
        print(f"Found {len(formatted_results)} results.")
        if not formatted_results:
            return []
        return formatted_results
        
    except Exception as e:
        print(f"Search failed: {e}")
        return []
