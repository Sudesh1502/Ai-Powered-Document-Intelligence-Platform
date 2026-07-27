"""
Centralized Azure OpenAI client factory.
All LLM calls in this project should use get_llm_client()
and AZURE_OPENAI_DEPLOYMENT_NAME from config.
"""
from openai import AzureOpenAI
from src.config.config import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_API_VERSION,
)


def get_llm_client() -> AzureOpenAI:
    """Returns a configured Azure OpenAI client instance."""
    if not AZURE_OPENAI_API_KEY or not AZURE_OPENAI_ENDPOINT:
        raise ValueError(
            "Missing Azure OpenAI credentials. Please ensure AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY are set in your .env file."
        )
    return AzureOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
    )
