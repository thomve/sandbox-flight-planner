import os

from langchain_anthropic import ChatAnthropic
from langchain_openai import AzureChatOpenAI


def get_llm(provider: str = "anthropic"):
    if provider == "anthropic":
        return ChatAnthropic(
            model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            max_tokens=4096,
        )
    elif provider == "azure_openai":
        return AzureChatOpenAI(
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
            max_tokens=4096,
        )
    else:
        raise ValueError(
            f"Unknown provider '{provider}'. Choose 'anthropic' or 'azure_openai'."
        )
