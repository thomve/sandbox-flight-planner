import os

from langchain_core.language_models import BaseChatModel
from langchain_openai import AzureChatOpenAI


def get_llm(provider: str = "huggingface") -> BaseChatModel:
    if provider == "azure_openai":
        return AzureChatOpenAI(
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
            max_tokens=4096,
        )

    if provider == "huggingface":
        from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

        model_id = os.getenv("HUGGINGFACE_MODEL", "Qwen/Qwen3-4B-Instruct-2507")
        endpoint = HuggingFaceEndpoint(
            repo_id=model_id,
            huggingfacehub_api_token=os.getenv("HUGGINGFACE_API_TOKEN"),
            task="text-generation",
            max_new_tokens=2048,
        )
        return ChatHuggingFace(llm=endpoint, verbose=False)

    raise ValueError(f"Unknown provider '{provider}'. Choose: azure_openai, huggingface")
