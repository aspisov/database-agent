"""
Visualization Agent Module

Handles visualization requests by generating code to create charts and graphs
from query results.
"""

import logging
import traceback
from typing import Any

from config.settings import get_settings
from models.response import AgentResponse
from pydantic import BaseModel, Field
from utils.llm_factory import LLMFactory

from agents.base import Agent


class ModifiedQuery(BaseModel):
    """Modifies query to retrieve data for visualization"""

    query: str = Field(
        description="Modified query to get relevant data from database"
    )


class VisualizationAgent(Agent):
    """
    Creates visualizations from data based on natural language descriptions.
    """

    def __init__(self):
        """Initialize the visualization agent."""
        self.settings = get_settings()
        self.llm = LLMFactory(provider=self.settings.default_llm_provider)
        self.logger = logging.getLogger(__name__)

    def process_query(
        self, query: str, context: Any | None = None
    ) -> AgentResponse:
        """
        Process a visualization request and prepare a query for data retrieval.

        Args:
            query: User's visualization request
            context: Optional conversation context

        Returns:
            Response with modified query for data retrieval
        """
        return AgentResponse.error_response(
            query_type="Visualization",
            query=query,
            error="Not implemented",
        )
