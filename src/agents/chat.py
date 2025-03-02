"""
Chat Agent Module

This module contains the ChatAgent responsible for handling general conversational
queries that don't require SQL or visualizations.
"""

import logging
from typing import Any, Dict, List, Optional

from src.agents.base import Agent
from src.models.response import AgentResponse, ChatResponse


class MockContext:
    """Temporary mock context class for development."""

    def __init__(self):
        self.messages = []

    def get_conversation_history(
        self, max_messages: int = 5
    ) -> List[Dict[str, Any]]:
        return self.messages[-max_messages:] if self.messages else []

    def add_message(self, role: str, content: str) -> Dict[str, Any]:
        msg = {"role": role, "content": content}
        self.messages.append(msg)
        return msg


class ChatAgent(Agent):
    """
    Chat Agent responsible for handling general conversational queries.
    """

    def __init__(self, model: str = "gpt-4"):
        """
        Initialize the Chat agent.

        Args:
            model: The LLM model to use for chat responses.
        """
        self.model = model
        self.logger = logging.getLogger(__name__)

    def process_query(
        self, query: str, context: Optional[Any] = None
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

        # Mock implementation
        mock_answer = (
            f"[MOCK] This is a simulated chat response. You asked: {query}"
        )

        # Update context if provided
        if context and hasattr(context, "add_message"):
            context.add_message("user", query)
            context.add_message("assistant", mock_answer)

        return ChatResponse(
            message="Chat query processed successfully.", answer=mock_answer
        )
