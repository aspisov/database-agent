"""
Visualization Agent Module

This module contains the VisualizationAgent responsible for generating
visualization code based on natural language queries and query results.
"""

import logging
from typing import Any, Dict, Optional

from src.agents.base import Agent
from src.models.response import AgentResponse, VisualizationResponse


class VisualizationAgent(Agent):
    """
    Visualization Agent responsible for generating visualizations from
    data based on natural language descriptions.
    """

    def __init__(self, model: str = "gpt-4"):
        """
        Initialize the visualization agent.

        Args:
            model: The LLM model to use for visualization code generation.
        """
        self.model = model
        self.logger = logging.getLogger(__name__)

    def process_query(
        self, query: str, context: Optional[Any] = None
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

        # Determine a mock visualization type based on keywords in the query
        viz_type = "bar"
        if (
            "line" in query.lower()
            or "trend" in query.lower()
            or "over time" in query.lower()
        ):
            viz_type = "line"
        elif "scatter" in query.lower() or "correlation" in query.lower():
            viz_type = "scatter"
        elif "pie" in query.lower() or "proportion" in query.lower():
            viz_type = "pie"

        # Create a mock visualization description
        mock_description = (
            f"This is a mock {viz_type} chart visualization for: {query}"
        )

        # Update context if available
        if context and hasattr(context, "add_message"):
            context.add_message("user", query)
            context.add_message(
                "assistant",
                f"I've created a {viz_type} chart based on your query: {query}",
            )

        return VisualizationResponse(
            message="Visualization created successfully.",
            visualization_type=viz_type,
            data={
                "type": viz_type,
                "description": mock_description,
                "mock_data": True,
            },
        )
