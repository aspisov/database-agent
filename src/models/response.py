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
    message: str = Field(
        description="A human-readable message describing the result"
    )
    error: str | None = Field(
        default=None, description="Error message if the operation failed"
    )

    @classmethod
    def error_response(cls, query_type: str, error: str) -> "AgentResponse":
        """Helper method to create an error response."""
        return cls(
            success=False,
            query_type=query_type,
            message=f"Error: {error}",
            error=error,
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
    df: str | None = Field(
        default=None,
        description="Executed query results as a pandas DataFrame",
    )


class VisualizationResponse(AgentResponse):
    """Response model specific to Visualization agent."""

    query_type: str = "Visualization"
    visualization_type: str | None = Field(
        default=None,
        description="The type of visualization generated (bar, line, etc.)",
    )
    image_data: str | None = Field(
        default=None, description="Base64-encoded image data if applicable"
    )


class ChatResponse(AgentResponse):
    """Response model specific to Chat agent."""

    query_type: str = "Chat"
    answer: str = Field(description="The answer to the user's question")
