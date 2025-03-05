"""
Text2SQL Agent Module

This module contains the Text2SQL agent responsible for converting natural language
queries into executable SQL queries for PostgreSQL.
"""

import logging
from typing import Literal, Type, cast, Any

from src.agents.base import Agent
from src.database.connector import DatabaseConnector
from src.models.response import AgentResponse, Text2SQLResponse
from src.models.context import Context
from config.settings import get_settings
from pydantic import BaseModel, Field
from src.prompts.text2sql_prompts import (
    TEXT2SQL_GENERATION_SYSTEM_PROMPT,
    TEXT2SQL_GENERATION_USER_PROMPT,
    TEXT2SQL_VERIFY_PROMPT,
    TEXT2SQL_VERIFY_USER_PROMPT,
)
from src.utils.llm_factory import LLMFactory


class SQLQuery(BaseModel):
    """SQL query response from the Text2SQL agent."""

    chain_of_thought: str = Field(
        description="The chain of thought process for the query"
    )
    sql_query: str = Field(description="The generated SQL query")
    explanation: str = Field(
        description="Explanation of your SQL query to a non-technical user",
    )


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

    def __init__(self, llm_provider: str = "openai"):
        """
        Initialize the Text2SQL agent.

        Args:
            llm_provider: The LLM provider to use ("openai" or "gigachat")
        """
        self.settings = get_settings()
        self.llm = LLMFactory(provider=llm_provider)
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
        logging.info(f"Verifying query: {query}")

        metadata = self.connector.get_text2sql_context()

        try:
            result: Any = self.llm.create_completion(
                system_prompt=TEXT2SQL_VERIFY_PROMPT,
                user_prompt=TEXT2SQL_VERIFY_USER_PROMPT.format(
                    query=query, metadata=metadata
                ),
                response_model=VerificationResult,
            )

            if result is None:
                return VerificationResult(
                    result="invalid",
                    explanation="Failed to parse verification result",
                )

            return result
        except Exception as e:
            logging.error(f"Error verifying query: {e}")
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
        logging.info(f"Generating SQL for query: {query}")

        metadata = self.connector.get_text2sql_context()

        try:
            result: Any = self.llm.create_completion(
                system_prompt=TEXT2SQL_GENERATION_SYSTEM_PROMPT,
                user_prompt=TEXT2SQL_GENERATION_USER_PROMPT.format(
                    query=query, metadata=metadata
                ),
                response_model=SQLQuery,
            )

            if result is None:
                raise ValueError("Failed to parse SQL query response")

            return result
        except Exception as e:
            logging.error(f"Error generating SQL query: {e}")
            raise

    def process_query(
        self, query: str, context: Any | None = None
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
        logging.info(f"Processing Text2SQL query: {query}")

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
                message=sql_query.explanation,
                sql_query=sql_query.sql_query,
                query_results=query_results,
            )

        except Exception as e:
            logging.error(f"Error processing Text2SQL query: {e}")
            return Text2SQLResponse(
                success=False,
                query=query,
                message="Error processing Text2SQL query",
                error=str(e),
            )
