"""
Query Router Module

This module contains the QueryRouter class responsible for classifying user queries
and routing them to the appropriate specialized agent (Text2SQL, Visualization, or Chat).
"""

import logging
import typing as tp
from pydantic import BaseModel, Field
from enum import Enum

from src.agents.base import Agent
from src.agents.chat import ChatAgent
from src.agents.text2sql import Text2SQLAgent
from src.agents.visualization import VisualizationAgent
from src.models.response import AgentResponse


class QueryType(str, Enum):
    """Enum for query types"""

    TEXT2SQL = "Text2SQL"
    VISUALIZATION = "Visualization"
    CHAT = "Chat"


class QueryClassification(BaseModel):
    """Classification result for user queries."""

    query_type: QueryType = Field(description="The type of query")
    confidence_score: float = Field(
        description="Confidence score between 0 and 1", ge=0.0, le=1.0
    )


class QueryRouter:
    """
    Query Router responsible for analyzing user queries and determining which
    specialized agent should handle them.
    """

    def __init__(self):
        """Initialize the QueryRouter with its agents."""
        self.logger = logging.getLogger(__name__)

        # Initialize specialized agents
        self.chat_agent = ChatAgent()
        self.text2sql_agent = Text2SQLAgent()
        self.visualization_agent = VisualizationAgent()

        # Default classification
        self.default_classification = QueryClassification(
            query_type=QueryType.CHAT, confidence_score=1.0
        )

    def classify_query(
        self, query: str, context: tp.Any | None = None
    ) -> QueryClassification:
        """
        Classify a user query into one of the predefined types.
        This is a simplified mock implementation.

        Args:
            query: The user's natural language query.
            context: Optional context information.

        Returns:
            QueryClassification: The classified query type with confidence score.
        """
        self.logger.info(f"Classifying query: {query}")

        # Simple keyword-based classification for the mock version
        query_lower = query.lower()

        if any(
            term in query_lower
            for term in [
                "sql",
                "query",
                "table",
                "select",
                "join",
                "database",
                "rows",
                "columns",
            ]
        ):
            return QueryClassification(
                query_type=QueryType.TEXT2SQL, confidence_score=0.9
            )
        elif any(
            term in query_lower
            for term in [
                "chart",
                "plot",
                "graph",
                "visualize",
                "bar",
                "line",
                "pie",
                "scatter",
                "trend",
            ]
        ):
            return QueryClassification(
                query_type=QueryType.VISUALIZATION, confidence_score=0.9
            )
        else:
            return QueryClassification(
                query_type=QueryType.CHAT, confidence_score=0.7
            )

    def route_query(
        self, query: str, context: tp.Any | None = None
    ) -> AgentResponse:
        """
        Route the query to the appropriate handler based on classification.

        Args:
            query: The user's natural language query.
            context: Optional context information.

        Returns:
            AgentResponse: A standardized response from the appropriate agent.
        """
        # Classify the query
        classification = self.classify_query(query, context)
        self.logger.info(
            f"Query classified as {classification.query_type} with confidence {classification.confidence_score}"
        )

        # Route to the appropriate agent
        if classification.query_type == QueryType.TEXT2SQL:
            return self.text2sql_agent.process_query(query, context)
        elif classification.query_type == QueryType.VISUALIZATION:
            return self.visualization_agent.process_query(query, context)
        else:
            return self.chat_agent.process_query(query, context)
