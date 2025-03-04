"""
Chat Agent Module

This module contains the ChatAgent responsible for handling general conversational
queries that don't require SQL or visualizations.
"""

import logging
import typing as tp

from config.settings import settings
from openai import OpenAI
from src.agents.base import Agent
from src.models.response import AgentResponse, ChatResponse
from src.prompts.chat_prompts import CHAT_SYSTEM_PROMPT


class ChatAgent(Agent):
    """
    Chat Agent responsible for handling general conversational queries.
    """

    def __init__(self):
        """
        Initialize the Chat agent.

        Args:
            model: The LLM model to use for chat responses.
        """
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.logger = logging.getLogger(__name__)

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
        self.logger.info(f"Processing chat query: {query}")

        try:
            response = self.client.chat.completions.create(
                model=settings.LOGIC_MODEL,
                messages=[
                    {"role": "system", "content": CHAT_SYSTEM_PROMPT},
                    {"role": "user", "content": query},
                ],
            )
            answer = response.choices[0].message.content or ""

            return ChatResponse(
                query=query,
                message="Chat query processed successfully.",
                answer=answer,
            )
        except Exception as e:
            self.logger.error(f"Error processing chat query: {e}")
            return ChatResponse.error_response(
                query_type="Chat",
                query=query,
                error=str(e),
            )
