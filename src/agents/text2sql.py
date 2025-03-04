"""
Text2SQL Agent Module

This module contains the Text2SQL agent responsible for converting natural language
queries into executable SQL queries for PostgreSQL.
"""

import logging
import typing as tp
from typing import Literal
from openai import OpenAI

from src.agents.base import Agent
from src.database.connector import DatabaseConnector
from src.models.response import AgentResponse, Text2SQLResponse
from src.models.context import Context
from config.settings import settings
from pydantic import BaseModel, Field
from src.prompts.text2sql_prompts import (
    TEXT2SQL_GENERATION_SYSTEM_PROMPT,
    TEXT2SQL_GENERATION_USER_PROMPT,
    TEXT2SQL_VERIFY_PROMPT,
    TEXT2SQL_VERIFY_USER_PROMPT,
)


class SQLQuery(BaseModel):
    """SQL query response from the Text2SQL agent."""

    chain_of_thought: str = Field(
        description="The chain of thought process for the query"
    )
    sql_query: str = Field(description="The generated SQL query")


class VerificationResult(BaseModel):
    """Result of the verification step."""

    result: Literal["valid", "requires_clarification", "invalid"] = Field(
        description="The result of the verification"
    )
    explanation: str = Field(
        description="Explanation of the verification result"
    )
    clarification_question: str | None = Field(
        default=None,
        description="Question to ask the user for clarification if result is 'requires_clarification'",
    )


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

    def _verify_query(
        self, query: str, context: Context | None = None
    ) -> VerificationResult:
        """
        Verify if the query is valid, requires clarification, or is invalid.

        Args:
            query: The user's natural language query.
            context: Optional context information.

        Returns:
            VerificationResult: The result of the verification.
        """
        self.logger.info(f"Verifying query: {query}")

        metadata = self.connector.get_text2sql_context()

        try:
            response = self.client.beta.chat.completions.parse(
                model=settings.TEXT2SQL_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": TEXT2SQL_VERIFY_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": TEXT2SQL_VERIFY_USER_PROMPT.format(
                            query=query, metadata=metadata
                        ),
                    },
                ],
                response_format=VerificationResult,
            )
            result = response.choices[0].message.parsed
            if result is None:
                return VerificationResult(
                    result="invalid",
                    explanation="Failed to parse verification result",
                )
            return result
        except Exception as e:
            self.logger.error(f"Error verifying query: {e}")
            return VerificationResult(
                result="invalid",
                explanation="Error during verification",
            )

    def _generate_sql(
        self, query: str, context: Context | None = None
    ) -> SQLQuery:
        """
        Generate an SQL query from a natural language query.

        Args:
            query: The user's natural language query.
            context: Optional context information.

        Returns:
            SQLQuery: The generated SQL query with chain of thought.
        """
        self.logger.info(f"Generating SQL for query: {query}")

        metadata = self.connector.get_text2sql_context()

        try:
            response = self.client.beta.chat.completions.parse(
                model=settings.TEXT2SQL_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": TEXT2SQL_GENERATION_SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": TEXT2SQL_GENERATION_USER_PROMPT.format(
                            query=query, metadata=metadata
                        ),
                    },
                ],
                response_format=SQLQuery,
            )
            result = response.choices[0].message.parsed
            if result is None:
                raise ValueError("Failed to parse SQL query response")
            return result
        except Exception as e:
            self.logger.error(f"Error generating SQL query: {e}")
            raise

    def process_query(
        self, query: str, context: tp.Any | None = None
    ) -> AgentResponse:
        """
        Process a natural language query and convert it to SQL.

        This method follows the Evaluator-Optimizer workflow pattern:
        1. First, evaluate the query using the _verify_query method (evaluator)
        2. Then, based on the verification result:
           - If valid, generate and execute the SQL (optimizer)
           - If requires clarification, return a clarification request
           - If invalid, return an error

        Args:
            query: The user's natural language query.
            context: Optional context information (e.g., schema information).

        Returns:
            AgentResponse: A standardized response with the generated SQL or error.
        """
        self.logger.info(f"Processing Text2SQL query: {query}")

        try:
            # Step 1: Verify the query (Evaluator)
            verification = self._verify_query(query, context)

            # Step 2: Process based on verification result (Optimizer)
            if verification.result == "invalid":
                return Text2SQLResponse(
                    success=False,
                    query=query,
                    message=verification.explanation,
                    error="Invalid query",
                )

            elif verification.result == "requires_clarification":
                return Text2SQLResponse.clarification_response(
                    query_type="Text2SQL",
                    query=query,
                    explanation=verification.explanation,
                    question=verification.clarification_question
                    or "Could you please clarify your query?",
                )

            # If valid, proceed with generating and executing SQL
            sql_query = self._generate_sql(query)

            # Execute the generated SQL query
            query_results = self.connector.execute_query(sql_query.sql_query)

            return Text2SQLResponse(
                success=True,
                query=query,
                message=sql_query.chain_of_thought,
                sql_query=sql_query.sql_query,
                query_results=query_results,
            )

        except Exception as e:
            self.logger.error(f"Error processing Text2SQL query: {e}")
            return Text2SQLResponse(
                success=False,
                query=query,
                message="Error processing Text2SQL query",
                error=str(e),
            )
