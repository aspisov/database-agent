from typing import Literal

from pydantic import BaseModel, Field


class QueryValidation(BaseModel):
    """Validation result for user queries"""

    status: Literal["valid", "invalid"]
    clarification_question: str | None = Field(
        default=None,
        description="Question to clarify the user's intent if the query is ambiguous or not clear",
    )


class SQLQuery(BaseModel):
    """Generated SQL query with chain of thought reasoning."""

    chain_of_thought: str = Field(
        description="Step-by-step reasoning process explaining how the SQL query was derived"
    )
    sql_query: str = Field(description="The executable SQL query in PostgreSQL syntax")


class SQLEvaluation(BaseModel):
    """Evaluation of the SQL query"""

    chain_of_thought: str = Field(
        description="Step-by-step reasoning process explaining how the SQL query was evaluated"
    )
    verdict: Literal["correct", "incorrect"]
    correction: str | None = Field(
        default=None,
        description="What should be done to improve the query, if it is incorrect",
    )


class FormattedResponse(BaseModel):
    """Formatted response for the user"""

    answer: str = Field(
        description="Well structured and clear answer to the user's question"
    )
    explanation: str = Field(
        description="A user-friendly explanation of how we arrived a the answer"
    )
