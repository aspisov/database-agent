"""
Response Models

This module contains the response models used by all agents in the system.
These models provide a standardized way to return responses to the user.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class AgentResponse(BaseModel):
    """Base response model for all agents."""

    success: bool = Field(
        default=True, description="Whether the agent operation was successful"
    )
    query_type: str = Field(description="The type of query that was processed")
    message: str = Field(
        description="A human-readable message describing the result"
    )
    data: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional data returned by the agent (e.g., SQL query, visualization data)",
    )
    error: Optional[str] = Field(
        default=None, description="Error message if the operation failed"
    )

    @classmethod
    def success_response(
        cls,
        query_type: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> "AgentResponse":
        """Helper method to create a successful response."""
        return cls(
            success=True,
            query_type=query_type,
            message=message,
            data=data or {},
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
    sql_query: Optional[str] = Field(
        default=None, description="The generated SQL query"
    )
    explanation: Optional[str] = Field(
        default=None, description="Explanation of the SQL query"
    )


class VisualizationResponse(AgentResponse):
    """Response model specific to Visualization agent."""

    query_type: str = "Visualization"
    visualization_type: Optional[str] = Field(
        default=None,
        description="The type of visualization generated (bar, line, etc.)",
    )
    image_data: Optional[str] = Field(
        default=None, description="Base64-encoded image data if applicable"
    )


class ChatResponse(AgentResponse):
    """Response model specific to Chat agent."""

    query_type: str = "Chat"
    answer: str = Field(description="The answer to the user's question")
