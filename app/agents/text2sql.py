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
from pydantic import BaseModel, Field

from agents.base import Agent
from database.connector import DatabaseConnector
from models.response import AgentResponse, Text2SQLResponse
from models.context import Context
from config.settings import get_settings
from prompts.prompt_manager import PromptManager
from utils.llm_factory import LLMFactory


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
        Verifies if the user query can be answered with the available database schema.

        Args:
            query: The natural language query to verify
            context: Optional context containing database connection and schema

        Returns:
            VerificationResult with validation status and explanation
        """
        try:
            logging.info(f"Verifying query: {query}")
            connector = DatabaseConnector()
            metadata = connector.get_text2sql_context()

            result: Any = self.llm.create_completion(
                system_prompt=PromptManager.get_text2sql_verify_prompt(),
                user_prompt=PromptManager.get_text2sql_verify_user_prompt(
                    query=query, metadata=str(metadata)
                ),
                response_model=VerificationResult,
            )

            # Ensure we have a valid result
            if not result:
                return VerificationResult(
                    validation_status=QueryValidationType.INVALID,
                    explanation="Failed to verify query",
                    clarification_question=None,
                )

            logging.info(f"Verification result: {result.validation_status}")
            return result
        except Exception as e:
            logging.error(f"Error in query verification: {e}")
            return VerificationResult(
                validation_status=QueryValidationType.INVALID,
                explanation=f"Error during verification: {str(e)}",
                clarification_question=None,
            )

    def _generate_sql(
        self, query: str, context: Context | None = None
    ) -> SQLQuery:
        """
        Generates SQL from the user's natural language query.

        Args:
            query: The natural language query to convert to SQL
            context: Optional context containing database connection and schema

        Returns:
            SQLQuery with the generated SQL and explanation
        """
        try:
            logging.info(f"Generating SQL for query: {query}")
            connector = DatabaseConnector()
            metadata = connector.get_text2sql_context()

            result: Any = self.llm.create_completion(
                system_prompt=PromptManager.get_text2sql_generation_system_prompt(),
                user_prompt=PromptManager.get_text2sql_generation_user_prompt(
                    query=query, metadata=str(metadata)
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
