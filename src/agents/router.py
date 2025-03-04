"""
Query Router Module

This module contains the QueryRouter class responsible for classifying user queries
and routing them to the appropriate specialized agent (Text2SQL, Visualization, or Chat).
"""

import logging
import typing as tp
from openai import OpenAI
from pydantic import BaseModel, Field
from enum import Enum

from config import settings
from src.agents.base import Agent
from src.agents.chat import ChatAgent
from src.agents.text2sql import Text2SQLAgent
from src.agents.visualization import VisualizationAgent
from src.models.response import AgentResponse
from config.settings import settings
from src.prompts.router_prompts import (
    CLASSIFY_SYSTEM_PROMPT,
    CLASSIFY_USER_PROMPT,
)


class QueryType(str, Enum):
    """Enum for query types"""

    TEXT2SQL = "Text2SQL"
    VISUALIZATION = "Visualization"
    CHAT = "Chat"


class QueryClassification(BaseModel):
    """Classification result for user queries."""

    query_type: QueryType = Field(description="The type of query")
    confidence_score: float = Field(
        description="Confidence score between 0 and 1"
    )


class QueryRouter:
    """
    Query Router responsible for analyzing user queries and determining which
    specialized agent should handle them.
    """

    def __init__(self):
        """Initialize the QueryRouter with its agents."""
        self.logger = logging.getLogger(__name__)

        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

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

        history = context.get_conversation_history() if context else []

        try:
            response = self.client.beta.chat.completions.parse(
                model=settings.ROUTER_MODEL,
                messages=[
                    {"role": "system", "content": CLASSIFY_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": CLASSIFY_USER_PROMPT.format(
                            query=query, history=history
                        ),
                    },
                ],
                response_format=QueryClassification,
            )
            return (
                response.choices[0].message.parsed
                or self.default_classification
            )
        except Exception as e:
            self.logger.error(f"Error classifying query: {e}")
            return self.default_classification

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
