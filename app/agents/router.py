"""
Query Router Module

Routes user queries to the appropriate specialized agent based on query type.
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
    """Types of queries the system can handle"""

    TEXT2SQL = "Text2SQL"
    VISUALIZATION = "Visualization"
    CHAT = "Chat"


class QueryClassification(BaseModel):
    """Classification result for user queries"""

    query_type: QueryType = Field(description="The type of query")
    confidence_score: float = Field(
        description="Confidence score between 0 and 1"
    )
    updated_query: str | None = Field(
        default=None,
        description="Updated query based on conversation context when clarifying previous queries",
    )


class QueryRouter:
    """
    Routes queries to the right specialized agent based on content analysis.
    """

    def __init__(self):
        """Initialize the QueryRouter with its specialized agents."""
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
        Analyze query to decide which agent should handle it.

        Args:
            query: User's query text
            context: Optional conversation context

        Returns:
            Classification with query type and confidence score
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
        Send the query to the right agent based on classification.

        Args:
            query: User's query text
            context: Optional conversation context

        Returns:
            Response from the appropriate specialized agent
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
