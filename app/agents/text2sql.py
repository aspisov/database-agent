"""
Text2SQL Agent Module

Converts natural language queries into executable SQL for PostgreSQL.
Uses a two-phase approach with verification and generation steps.
"""

import logging
import traceback
from enum import Enum
from typing import Any

from config.settings import get_settings
from database.connector import DatabaseConnector
from models.context import Context
from models.response import AgentResponse, Text2SQLResponse
from prompts.prompt_manager import PromptManager
from pydantic import BaseModel, Field
from utils.llm_factory import LLMFactory

from agents.base import Agent


class SQLQuery(BaseModel):
    """Generated SQL query with reasoning and explanation."""

    reasoning: str = Field(
        description="Step-by-step reasoning process explaining how the SQL query was derived"
    )
    sql_query: str = Field(
        description="The executable SQL query in PostgreSQL syntax"
    )
    explanation: str = Field(
        description="User-friendly explanation of what the query does"
    )


class QueryValidationType(Enum):
    """Validation status for natural language queries."""

    VALID = "valid"
    REQUIRES_CLARIFICATION = "requires_clarification"
    INVALID = "invalid"


class VerificationResult(BaseModel):
    """Result from query verification phase."""

    validation_status: QueryValidationType = Field(
        description="Whether the query can be answered with the available schema"
    )
    explanation: str = Field(
        description="Explanation of the verification result"
    )
    clarification_question: str | None = Field(
        default=None,
        description="Question to ask user when more information is needed"
    )


class Text2SQLAgent(Agent):
    """
    Transforms natural language into optimized SQL queries.
    
    Uses a two-phase approach:
    1. Verification: Validates if query can be answered with available schema
    2. Generation: Creates SQL based on the validated query
    """

    def __init__(self):
        """Initialize the Text2SQL agent with LLM and database connector."""
        self.settings = get_settings()
        self.llm = LLMFactory(provider=self.settings.default_llm_provider)
        self.connector = DatabaseConnector()

    def _verify_query(
        self, query: str, context: Context | None = None
    ) -> VerificationResult:
        """
        Check if query can be answered with available database schema.

        Args:
            query: Natural language query to verify
            context: Optional database context

        Returns:
            Verification result with status and explanation
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
            logging.error(traceback.format_exc())
            return VerificationResult(
                validation_status=QueryValidationType.INVALID,
                explanation=f"Error during verification: {str(e)}",
                clarification_question=None,
            )

    def _generate_sql(
        self, query: str, context: Context | None = None
    ) -> SQLQuery:
        """
        Generate SQL from natural language query.

        Args:
            query: Natural language query 
            context: Optional database context

        Returns:
            SQLQuery with generated SQL and explanation
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
            logging.error(f"Error generating SQL query: {e}")
            logging.error(traceback.format_exc())
            raise ValueError(f"Failed to generate SQL: {e}")

    def process_query(
        self, query: str, context: Any | None = None
    ) -> AgentResponse:
        """
        Process user query through verification, SQL generation, and execution.
        
        Follows an evaluator-optimizer workflow:
        1. First verifies if query is answerable
        2. Then generates and executes SQL if valid
        
        Args:
            query: User's natural language query
            context: Optional conversation context

        Returns:
            Response with SQL, results, or clarification request
        """
        logging.info(f"Processing Text2SQL query: '{query}'")

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
