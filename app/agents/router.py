"""
Query Router Module

This module contains the QueryRouter class responsible for classifying user queries
and routing them to the appropriate specialized agent (Text2SQL, Visualization, or Chat).
"""

import logging
import traceback
import typing as tp
from enum import Enum

from config.settings import get_settings
from models.response import AgentResponse
from prompts.prompt_manager import PromptManager
from pydantic import BaseModel, Field
from utils.llm_factory import LLMFactory

from agents.chat import ChatAgent
from agents.text2sql import Text2SQLAgent
from agents.visualization import VisualizationAgent


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
    updated_query: str | None = Field(
        default=None,
        description="Updated query based on chat history context when the query is a clarification of previous conversation",
    )


class QueryRouter:
    """
    Query Router responsible for analyzing user queries and determining which
    specialized agent should handle them.
    """

    def __init__(self):
        """Initialize the QueryRouter with its agents."""
        self.settings = get_settings()

        self.llm = LLMFactory(provider=self.settings.default_llm_provider)

        # Initialize specialized agents
        self.chat_agent = ChatAgent()
        self.text2sql_agent = Text2SQLAgent()
        self.visualization_agent = VisualizationAgent()

        # Default classification
        self.default_classification = QueryClassification(
            query_type=QueryType.CHAT, confidence_score=1.0, updated_query=None
        )

    def classify_query(
        self, query: str, context: tp.Any | None = None
    ) -> QueryClassification:
        """
        Classify user query to determine which agent should handle it.

        Args:
            query: The user's query
            context: Optional context for the query

        Returns:
            Classification result with query type and confidence score
        """
        # Format chat history as string if provided in context
        history = ""
        if (
            context
            and hasattr(context, "chat_history")
            and context.chat_history
        ):
            history = "\n".join(
                [f"{msg.role}: {msg.content}" for msg in context.chat_history]
            )

        try:
            response = self.llm.create_completion(
                system_prompt=PromptManager.get_router_system_prompt(),
                user_prompt=PromptManager.get_router_user_prompt(
                    query=query, history=history
                ),
                response_model=QueryClassification,
            )
            return (
                QueryClassification(**response.__dict__)
                if response
                else self.default_classification
            )
        except Exception as e:
            logging.error(f"Error in query classification: {e}")
            logging.error(traceback.format_exc())
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
        logging.info(
            f"Query classified as {classification.query_type} with confidence {classification.confidence_score}"
        )

        # If we have an updated query based on context, use it instead
        effective_query = classification.updated_query or query
        if classification.updated_query:
            logging.info(f"Using updated query: {effective_query}")

        # Route to the appropriate agent
        if classification.query_type == QueryType.TEXT2SQL:
            return self.text2sql_agent.process_query(effective_query, context)
        elif classification.query_type == QueryType.VISUALIZATION:
            return self.visualization_agent.process_query(
                effective_query, context
            )
        else:
            return self.chat_agent.process_query(effective_query, context)
