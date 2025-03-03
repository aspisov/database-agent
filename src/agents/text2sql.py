"""
Text2SQL Agent Module

This module contains the Text2SQL agent responsible for converting natural language
queries into executable SQL queries for PostgreSQL.
"""

import logging
import typing as tp

from openai import OpenAI

from src.agents.base import Agent
from src.database.connector import DatabaseConnector
from src.models.response import AgentResponse, Text2SQLResponse
from config.settings import settings
from pydantic import BaseModel, Field
from src.prompts.text2sql_prompts import (
    TEXT2SQL_SYSTEM_PROMPT,
    TEXT2SQL_USER_PROMPT,
)


class SQLQuery(BaseModel):
    """SQL query response from the Text2SQL agent."""

    chain_of_thought: str = Field(
        description="The chain of thought process for the query"
    )
    sql_query: str = Field(description="The generated SQL query")


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
        self.logger = logging.getLogger(__name__)
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.connector = DatabaseConnector()

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

        metadata = self.connector.get_text2sql_context()
        self.logger.debug(f"Metadata: {metadata}")

        try:
            response = self.client.beta.chat.completions.parse(
                model=settings.TEXT2SQL_MODEL,
                messages=[
                    {"role": "system", "content": TEXT2SQL_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": TEXT2SQL_USER_PROMPT.format(
                            query=query, metadata=metadata
                        ),
                    },
                ],
                response_format=SQLQuery,
            )
            sql_query = response.choices[0].message.parsed

            return Text2SQLResponse(
                success=True,
                message=sql_query.chain_of_thought,
                sql_query=sql_query.sql_query,
                query_results=self.connector.execute_query(
                    sql_query.sql_query
                ),
            )
        except Exception as e:
            self.logger.error(f"Error processing Text2SQL query: {e}")
            return AgentResponse.error(
                message="Error processing Text2SQL query",
                error=e,
            )
