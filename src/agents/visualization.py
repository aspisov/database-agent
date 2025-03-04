"""
Visualization Agent Module

This module contains the VisualizationAgent responsible for generating
visualization code based on natural language queries and query results.
"""

import logging
import typing as tp
from openai import OpenAI
from pydantic import BaseModel, Field

from src.agents.base import Agent
from src.models.response import AgentResponse
from config.settings import settings
from src.prompts.visualization_prompt import MODIFY_QUERY_SYSTEM_PROMPT


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
            model: The LLM model to use for visualization code generation.
        """
        self.client = OpenAI(api_key=settings.VISUALIZATION_MODEL)
        self.logger = logging.getLogger(__name__)

    def process_query(
        self, query: str, context: tp.Any | None = None
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
            error="Visualization agent is not implemented yet",
        )
