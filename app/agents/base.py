"""
Base Agent Module

Defines the base Agent class that all specialized agents will inherit from.
"""

import typing as tp
from abc import ABC, abstractmethod

from models.response import AgentResponse


class Agent(ABC):
    """
    Base Agent abstract class that all specialized agents inherit from.
    
    Provides a common interface for processing user queries across different
    agent types in the system.
    """

    @abstractmethod
    def process_query(
        self, query: str, context: tp.Any | None = None
    ) -> AgentResponse:
        """
        Process a user query and return a response.

        Args:
            query: The user's natural language query
            context: Optional context info (conversation history, etc.)

        Returns:
            AgentResponse: A structured response object
        """
        pass
