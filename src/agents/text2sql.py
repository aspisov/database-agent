"""
Text2SQL Agent Module

This module contains the Text2SQL agent responsible for converting natural language
queries into executable SQL queries for PostgreSQL databases. The agent follows an
evaluator-optimizer pattern, first verifying if a query can be answered with the
available schema, then generating and executing the appropriate SQL.
"""

import logging
from typing import Any
from enum import Enum
from pprint import pprint
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
    """Structured output for SQL generation containing the query and reasoning."""

    reasoning: str = Field(
        description="Step-by-step reasoning process explaining how the SQL query was derived"
    )
    sql_query: str = Field(
        description="The executable SQL query in PostgreSQL syntax"
    )
    explanation: str = Field(
        description="User-friendly explanation of what the query does and how it addresses the question"
    )


class QueryValidationType(Enum):
    """Classification of natural language query validation status."""

    VALID = "valid"
    REQUIRES_CLARIFICATION = "requires_clarification"
    INVALID = "invalid"


class VerificationResult(BaseModel):
    """Structured output from the query verification step."""

    validation_status: QueryValidationType = Field(
        description="Determination of whether the query can be answered with the available schema"
    )
    explanation: str = Field(
        description="Detailed explanation of the verification result, including reasoning"
    )
    clarification_question: str | None = Field(
        default=None,
        description="Specific question to ask the user when additional information is needed to formulate an SQL query",
    )


class Text2SQLAgent(Agent):
    """
    Text2SQL Agent that transforms natural language queries into executable SQL.

    This agent uses a two-phase approach:
    1. Verification: Checks if the query can be answered with the available database schema
    2. Generation: Creates an optimized SQL query based on the validated natural language query

    The agent connects to a database to execute the generated queries and return results.
    """

    def __init__(self):
        """
        Initialize the Text2SQL agent with language model and database connections.

        Args:
            llm_provider: The language model provider to use ("openai" or "gigachat")
        """
        self.settings = get_settings()
        self.llm = LLMFactory(provider=self.settings.default_llm_provider)
        self.logger = logging.getLogger(__name__)
        self.connector = DatabaseConnector()

    def _verify_query(
        self, query: str, context: Context | None = None
    ) -> VerificationResult:
        """
        Verify if the natural language query can be answered with the available database schema.

        This method checks if:
        - The query refers to tables and columns that exist in the database
        - The required information is available in the schema
        - The user's intent is clear enough to generate SQL

        Args:
            query: The user's natural language query
            context: Optional conversation context for resolving ambiguous references

        Returns:
            VerificationResult: Structured result with validation status and explanation
        """
        self.logger.info(f"Verifying query: '{query}'")

        # Get database schema and metadata
        metadata = self.connector.get_text2sql_context()

        try:
            # Type annotation to help with type checking
            result: Any = self.llm.create_completion(
                system_prompt=TEXT2SQL_VERIFY_PROMPT,
                user_prompt=TEXT2SQL_VERIFY_USER_PROMPT.format(
                    query=query, metadata=metadata
                ),
                response_model=VerificationResult,
            )

            if result is None:
                return VerificationResult(
                    validation_status=QueryValidationType.INVALID,
                    explanation="Failed to verify query due to language model error",
                )

            # Return the verification result
            return result  # type: ignore
        except Exception as e:
            self.logger.error(f"Error verifying query: {e}")
            return VerificationResult(
                validation_status=QueryValidationType.INVALID,
                explanation=f"Verification error: {e}",
            )

    def _generate_sql(
        self, query: str, context: Context | None = None
    ) -> SQLQuery:
        """
        Generate a SQL query from a validated natural language query.

        This method:
        1. Uses a language model to translate the natural language to SQL
        2. Ensures the generated SQL is compatible with PostgreSQL
        3. Returns both the query and explanation for transparency

        Args:
            query: The user's validated natural language query
            context: Optional conversation context for resolving references

        Returns:
            SQLQuery: Structured result with SQL query, reasoning process and explanation

        Raises:
            ValueError: If SQL generation fails or returns invalid SQL
        """
        self.logger.info(f"Generating SQL for query: '{query}'")

        # Get database schema and metadata
        metadata = self.connector.get_text2sql_context()
        pprint(metadata)

        try:
            # Type annotation to help with type checking
            result: Any = self.llm.create_completion(
                system_prompt=TEXT2SQL_GENERATION_SYSTEM_PROMPT,
                user_prompt=TEXT2SQL_GENERATION_USER_PROMPT.format(
                    query=query, metadata=metadata
                ),
                response_model=SQLQuery,
            )

            if result is None:
                raise ValueError(
                    "SQL generation failed: empty response from language model"
                )

            # Return the generated SQL query
            return result  # type: ignore
        except Exception as e:
            self.logger.error(f"Error generating SQL query: {e}")
            raise ValueError(f"Failed to generate SQL: {e}")

    def process_query(
        self, query: str, context: Any | None = None
    ) -> AgentResponse:
        """
        Process a natural language query through validation, SQL generation, and execution.

        This method follows the Evaluator-Optimizer workflow pattern:
        1. First, evaluate the query using the _verify_query method (evaluator)
        2. Then, based on the verification result:
           - If valid, generate and execute the SQL (optimizer)
           - If clarification needed, return a clarification request
           - If invalid, return an informative error message

        Args:
            query: The user's natural language query
            context: Optional conversation context for resolving references

        Returns:
            AgentResponse: A standardized response containing SQL, results, or error information
        """
        self.logger.info(f"Processing Text2SQL query: '{query}'")

        try:
            # Step 1: Verify the query (Evaluator phase)
            verification = self._verify_query(query, context)

            # Step 2: Process based on verification result (Optimizer phase)
            if verification.validation_status == QueryValidationType.INVALID:
                return Text2SQLResponse(
                    success=False,
                    query=query,
                    message=verification.explanation,
                    error="The query cannot be answered with the available database schema",
                )

            elif (
                verification.validation_status
                == QueryValidationType.REQUIRES_CLARIFICATION
            ):
                return Text2SQLResponse.clarification_response(
                    query_type="Text2SQL",
                    query=query,
                    explanation=verification.explanation,
                    question=verification.clarification_question
                    or "Could you please provide more specific details for your query?",
                )

            # Step 3: Generate and execute SQL for valid queries
            sql_query = self._generate_sql(query)

            # Execute the generated SQL query against the database
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
