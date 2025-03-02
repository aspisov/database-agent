"""
Base Agent Module

This module defines the base Agent class that all specialized agents inherit from.
"""

from abc import ABC, abstractmethod
import typing as tp

from src.models.context import Context
from src.models.response import AgentResponse


class Agent(ABC):
    """
    Base Agent abstract class that defines the interface for all specialized agents.

    All agents must implement the process_query method, which takes a query string
    and optional context and returns an AgentResponse.
    """

    @abstractmethod
    def process_query(
        self, query: str, context: tp.Any | None = None
    ) -> AgentResponse:
        """
        Process a user query and return a response.

        Args:
            query: The user's natural language query.
            context: Optional context information (e.g., conversation history).

        Returns:
            AgentResponse: A standardized response object with the result.
        """
        pass
