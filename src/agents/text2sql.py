"""
Text2SQL Agent Module

This module contains the Text2SQL agent responsible for converting natural language
queries into executable SQL queries for PostgreSQL.
"""

import logging
import typing as tp

from src.agents.base import Agent
from src.models.response import AgentResponse, Text2SQLResponse
from config.settings import settings


class Text2SQLAgent(Agent):
    """
    Text2SQL Agent responsible for converting natural language queries into
    executable SQL for PostgreSQL.
    """

    def __init__(self):
        """
        Initialize the Text2SQL agent.

        Args:
            model: The LLM model to use for SQL generation.
        """
        self.model = settings.TEXT2SQL_MODEL
        self.logger = logging.getLogger(__name__)

    def process_query(
        self, query: str, context: tp.Any | None = None
    ) -> AgentResponse:
        """
        Process a natural language query and convert it to SQL.

        Args:
            query: The user's natural language query.
            context: Optional context information (e.g., schema information).

        Returns:
            AgentResponse: A standardized response with the generated SQL.
        """
        self.logger.info(f"Processing Text2SQL query: {query}")

        # Generate a mock SQL query
        mock_sql = (
            f"SELECT * FROM users WHERE description LIKE '%{query}%' LIMIT 10;"
        )
        mock_explanation = f"This is a mock SQL query that searches for '{query}' in the users table."

        # Update context if available
        if context and hasattr(context, "update_current_sql"):
            context.update_current_sql(mock_sql)

        if context and hasattr(context, "add_message"):
            context.add_message("user", query)
            context.add_message(
                "assistant", f"SQL: {mock_sql}\n\n{mock_explanation}"
            )

        return Text2SQLResponse(
            message="SQL query generated successfully.",
            sql_query=mock_sql,
            explanation=mock_explanation,
        )
