from langchain_openai import ChatOpenAI
from langchain_gigachat import GigaChat
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, SecretStr
from typing import Type, Dict, Any, Optional, Union
import os

from config.settings import get_settings


class LLMFactory:
    def __init__(self, provider: str):
        self.provider = provider
        self.settings = get_settings()
        self.llm = self._initialize_llm(provider)

    def _initialize_llm(self, provider: str):
        if provider == "openai":
            # Create ChatOpenAI client with proper settings
            kwargs = {
                "model": self.settings.openai.model,
                "temperature": self.settings.openai.temperature,
                "max_retries": self.settings.openai.max_retries,
            }

            # Only add max_tokens if it's not None
            if self.settings.openai.max_tokens is not None:
                kwargs["max_tokens"] = self.settings.openai.max_tokens

            # Use the API key from settings
            if self.settings.openai.api_key:
                kwargs["api_key"] = self.settings.openai.api_key

            return ChatOpenAI(**kwargs)
        elif provider == "gigachat":
            # Create GigaChat client with proper settings
            kwargs = {
                "model": self.settings.gigachat.model,
                "temperature": self.settings.gigachat.temperature,
            }

            # Only add max_tokens if it's not None
            if self.settings.gigachat.max_tokens is not None:
                kwargs["max_tokens"] = self.settings.gigachat.max_tokens

            # Use the API key from settings
            if self.settings.gigachat.api_key:
                kwargs["credentials"] = self.settings.gigachat.api_key

            return GigaChat(**kwargs)
        else:
            raise ValueError(f"Provider {provider} not supported")

    def create_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Optional[Type[BaseModel]] = None,
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
            return self.llm.invoke(messages)
