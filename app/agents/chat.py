"""
Chat Agent Module

This module contains the ChatAgent responsible for handling general conversational
queries that don't require SQL or visualizations.
"""

import logging
import typing as tp

from config.settings import get_settings
from agents.base import Agent
from models.response import AgentResponse, ChatResponse
from prompts.prompt_manager import PromptManager
from utils.llm_factory import LLMFactory


class ChatAgent(Agent):
    """
    Chat Agent responsible for handling general conversational queries.
    """

    def __init__(self):
        """
        Initialize the Chat agent.

        Args:
            llm_provider: The LLM provider to use ("openai" or "gigachat")
        """
        self.settings = get_settings()
        self.llm = LLMFactory(provider=self.settings.default_llm_provider)

    def process_query(
        self, query: str, context: tp.Any | None = None
    ) -> AgentResponse:
        """
        Process a general chat query and return a response.

        Args:
            query: The user's natural language query.
            context: Optional context information (conversation history).

        Returns:
            AgentResponse: A standardized response with the chat answer.
        """
        logging.info(f"Processing chat query: {query}")

        try:
            response = self.llm.create_completion(
                system_prompt=PromptManager.get_chat_system_prompt(),
                user_prompt=query,
            )

            # Convert response to string if it's not already
            answer = str(response) if response is not None else ""

            return ChatResponse(
                query=query,
                message="Chat query processed successfully.",
                answer=answer,
            )
        except Exception as e:
            logging.error(f"Error processing chat query: {e}")
            return AgentResponse.error_response(
                query_type="Chat",
                query=query,
                error=str(e),
            )
