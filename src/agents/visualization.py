"""
Visualization Agent Module

This module contains the VisualizationAgent responsible for generating
visualization code based on natural language queries and query results.
"""

import logging
from typing import Any
from pydantic import BaseModel, Field

from src.agents.base import Agent
from src.models.response import AgentResponse
from config.settings import get_settings
from src.prompts.visualization_prompt import MODIFY_QUERY_SYSTEM_PROMPT
from src.utils.llm_factory import LLMFactory


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

    def __init__(self, llm_provider: str = "openai"):
        """
        Initialize the visualization agent.

        Args:
            llm_provider: The LLM provider to use ("openai" or "gigachat")
        """
        self.settings = get_settings()
        self.llm = LLMFactory(provider=llm_provider)
        self.logger = logging.getLogger(__name__)

    def process_query(
        self, query: str, context: Any | None = None
    ) -> AgentResponse:
        """
        Process a visualization query and generate a visualization description.

        Args:
            query: The user's natural language query
            context: Optional context information (e.g., query results)

        Returns:
            AgentResponse: A standardized response with visualization details
        """
        self.logger.info(f"Processing visualization query: {query}")

        return AgentResponse.error_response(
            query_type="Visualization",
            query=query,
            error="Visualization agent is not implemented yet",
        )
