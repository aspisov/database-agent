from typing import Type

from config.settings import get_settings
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_gigachat.chat_models import GigaChat
from langchain_openai import ChatOpenAI
from pydantic import BaseModel


class LLMFactory:
    def __init__(self, provider: str):
        self.provider = provider
        self.settings = get_settings()
        self.llm = self._initialize_llm(provider)

    def _initialize_llm(self, provider: str):
        if provider == "openai":
            kwargs = {
                "api_key": self.settings.openai.api_key,
                "model": self.settings.openai.model,
                "temperature": self.settings.openai.temperature,
                "top_p": self.settings.openai.top_p,
                "max_tokens": self.settings.openai.max_tokens,
                "timeout": self.settings.openai.timeout,
            }
            return ChatOpenAI(**kwargs)
        elif provider == "gigachat":
            kwargs = {
                "scope": self.settings.gigachat.scope,
                "credentials": self.settings.gigachat.api_key,
                "model": self.settings.gigachat.model,
                "verify_ssl_certs": False,
                "temperature": self.settings.gigachat.temperature,
                "top_p": self.settings.gigachat.top_p,
                "max_tokens": self.settings.gigachat.max_tokens,
                "timeout": self.settings.gigachat.timeout,
            }
            return GigaChat(**kwargs)
        else:
            raise ValueError(f"Provider {provider} not supported")

    def create_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[BaseModel] | None = None,
    ):
        """
        Create a completion using the configured LLM.

        Args:
            system_prompt: The system prompt to use
            user_prompt: The user prompt to use
            response_model: A Pydantic model class (not an instance) to parse the response

        Returns:
            Either a string response or a structured output based on the response_model
        """
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        if response_model:
            return self.llm.with_structured_output(response_model).invoke(
                messages
            )
        else:
            return self.llm.invoke(messages).content
