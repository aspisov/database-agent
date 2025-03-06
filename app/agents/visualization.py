"""
Visualization Agent Module

This module contains the VisualizationAgent responsible for generating
visualization code based on natural language queries and query results.
"""

import logging
from typing import Any

from config.settings import get_settings
from models.response import AgentResponse
from pydantic import BaseModel, Field
from utils.llm_factory import LLMFactory

from agents.base import Agent


class ModifiedQuery(BaseModel):
    """Modifies visualization query for the Text2SQL agent to recieve desired dataframe"""

    query: str = Field(
        description="Modified query that would recieve relevant data from database"
    )


class VisualizationAgent(Agent):
    """
    Visualization Agent responsible for generating visualizations from
    data based on natural language descriptions.
    """

    def __init__(self):
        """
        Initialize the visualization agent.

        Args:
            llm_provider: The LLM provider to use ("openai" or "gigachat")
        """
        self.settings = get_settings()
        self.llm = LLMFactory(provider=self.settings.default_llm_provider)
        self.logger = logging.getLogger(__name__)

    def process_query(
        self, query: str, context: Any | None = None
    ) -> AgentResponse:
        """
        Process a visualization query and modify it for the Text2SQL agent.

        Args:
            query: The user's visualization request
            context: Optional context for the query

        Returns:
            AgentResponse containing the modified query
        """
        return AgentResponse.error_response(
            query_type="Visualization",
            query=query,
            error="Not implemented",
        )
