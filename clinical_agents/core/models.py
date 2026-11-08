import os
from typing import Optional, Any
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage


class MockClinicalChatModel(BaseChatModel):
    """
    Fallback/offline clinical model for development and automated testing
    when external LLM API keys are not yet provided.
    """
    model_name: str = "mock-clinical-v1"

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        # Default mock response - specialists can override or parse
        return AIMessage(content="Clinical analysis complete.")

    @property
    def _llm_type(self) -> str:
        return "mock-clinical"


def get_chat_model(model_name: Optional[str] = None, temperature: float = 0.1) -> Any:
    """
    Factory function for multi-model instantiation.
    Supports switching providers per agent via configuration.
    Falls back gracefully to MockClinicalChatModel if credentials are not configured.
    """
    model_name = model_name or os.getenv("DEFAULT_LLM_MODEL", "mock")

    # 1. OpenAI
    if model_name.startswith("gpt") or model_name.startswith("openai"):
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(model=model_name, temperature=temperature)
        except Exception:
            pass

    # 2. Anthropic
    if model_name.startswith("claude") or model_name.startswith("anthropic"):
        try:
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(model=model_name, temperature=temperature)
        except Exception:
            pass

    # 3. Google Gemini
    if model_name.startswith("gemini"):
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(model=model_name, temperature=temperature)
        except Exception:
            pass

    # 4. Ollama (local open-source)
    if model_name.startswith("ollama"):
        try:
            from langchain_community.chat_models import ChatOllama
            actual_model = model_name.split(":", 1)[1] if ":" in model_name else "llama3"
            return ChatOllama(model=actual_model, temperature=temperature)
        except Exception:
            pass

    # Default: Safe fallback mock model
    return MockClinicalChatModel(model_name=model_name)
