"""
Response Models

This module contains the response models used by all agents in the system.
These models provide a standardized way to return responses to the user.
"""

import typing as tp
from pydantic import BaseModel, Field
import pandas as pd


class AgentResponse(BaseModel):
    """Base response model for all agents."""

    success: bool = Field(
        default=True, description="Whether the agent operation was successful"
    )
    query_type: str = Field(description="The type of query that was processed")
    query: str = Field(description="The user's query")
    message: str = Field(
        description="A human-readable message describing the result"
    )
    error: str | None = Field(
        default=None, description="Error message if the operation failed"
    )
    needs_clarification: bool = Field(
        default=False,
        description="Whether clarification is needed from the user",
    )
    clarification_question: str | None = Field(
        default=None, description="Question to ask the user for clarification"
    )

    @classmethod
    def error_response(
        cls, query_type: str, query: str, error: str
    ) -> "AgentResponse":
        """Helper method to create an error response."""
        return cls(
            success=False,
            query_type=query_type,
            query=query,
            message=f"Error: {error}",
            error=error,
        )

    @classmethod
    def clarification_response(
        cls, query_type: str, query: str, explanation: str, question: str
    ) -> "AgentResponse":
        """Helper method to create a clarification response."""
        return cls(
            success=False,
            query_type=query_type,
            query=query,
            message=explanation,
            needs_clarification=True,
            clarification_question=question,
        )


class Text2SQLResponse(AgentResponse):
    """Response model specific to Text2SQL agent."""

    query_type: str = "Text2SQL"
    explanation: str | None = Field(
        default=None, description="Explanation of the SQL query"
    )
    sql_query: str | None = Field(
        default=None, description="The generated SQL query"
    )
    query_results: dict[str, tp.Any] | None = Field(
        default=None,
        description="Dictionary with query results and metadata",
    )


class ChatResponse(AgentResponse):
    """Response model specific to Chat agent."""

    query_type: str = "Chat"
    answer: str = Field(description="The answer to the user's question")
