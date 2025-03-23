import os
import webbrowser
from pathlib import Path
from pprint import pprint
from typing import Any, Literal

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from app.database.connector import DatabaseConnector
from app.prompts.prompt_manager import PromptManager

load_dotenv()

# ------------------------------------------------------------
# Models
# ------------------------------------------------------------


class QueryValidation(BaseModel):
    """Validation result for user queries"""

    status: Literal["valid", "invalid", "requires_clarification"]
    clarification_question: str | None = Field(
        default=None,
        description="Question to clarify the user's intent if the query is invalid or requires clarification",
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
    fix: str | None = Field(
        default=None,
        description="What should be done to improve the query, if it is incorrect",
    )


llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
validator = llm.with_structured_output(QueryValidation)
sql_generator = llm.with_structured_output(SQLQuery)
evaluator = llm.with_structured_output(SQLEvaluation)

# ------------------------------------------------------------
# Workflow
# ------------------------------------------------------------


class State(TypedDict):
    """State for the workflow"""

    user_query: str
    connector: DatabaseConnector
    user_query_status: Literal["valid", "invalid", "requires_clarification"] | None
    user_query_clarification_question: str | None
    sql_query: str | None
    sql_query_status: Literal["correct", "incorrect"] | None
    sql_query_fix: str | None


def validate_query_llm_call(state: State):
    """Validate the user query"""
    system_prompt = PromptManager.get_text2sql_validation_system_prompt()

    context: dict[str, Any] = state["connector"].get_text2sql_context()
    metadata_str = str(context) if isinstance(context, dict) else context

    user_prompt = PromptManager.get_text2sql_validation_user_prompt(
        query=state["user_query"], metadata=metadata_str
    )

    result = validator.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    )
    output = (
        QueryValidation.model_validate(result)
        if not isinstance(result, QueryValidation)
        else result
    )

    return {
        "user_query_status": output.status,
        "user_query_clarification_question": output.clarification_question,
    }


def route_validation(state: State):
    """Route the user query to the appropriate agent"""
    if state["user_query_status"] == "valid":
        return "valid"
    elif state["user_query_status"] == "invalid":
        return "invalid"
    elif state["user_query_status"] == "requires_clarification":
        return "requires_clarification"


def ask_clarification(state: State):
    """Ask the user for clarification"""
    print(state["user_query_clarification_question"])
    user_query = input("> ")
    updated_user_query = (
        state["user_query"]
        + "\n"
        + f"<Clarification question> {state['user_query_clarification_question']}"
        + "\n"
        + user_query
    )

    return {"user_query": updated_user_query}


def generate_sql_query_llm_call(state: State):
    """Generate a SQL query from the user query"""
    system_prompt = PromptManager.get_text2sql_generation_system_prompt()

    context: dict[str, Any] = state["connector"].get_text2sql_context()
    metadata_str = str(context) if isinstance(context, dict) else context

    user_prompt = PromptManager.get_text2sql_generation_user_prompt(
        query=state["user_query"],
        metadata=metadata_str,
        sql_query=state.get("sql_query", ""),
        fix=state.get("sql_query_fix", ""),
    )

    result = sql_generator.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    )
    output = (
        SQLQuery.model_validate(result) if not isinstance(result, SQLQuery) else result
    )

    return {"sql_query": output.sql_query}


def evaluate_sql_query_llm_call(state: State):
    """Evaluate the SQL query"""
    if state["sql_query"] is None:
        raise ValueError("SQL query cannot be None when evaluating")

    connector = DatabaseConnector()
    execution_result = connector.execute_query(state["sql_query"])

    system_prompt = PromptManager.get_text2sql_evaluation_system_prompt()

    context: dict[str, Any] = state["connector"].get_text2sql_context()
    metadata_str = str(context) if isinstance(context, dict) else context

    execution_result_str = (
        str(execution_result)
        if isinstance(execution_result, dict)
        else execution_result
    )

    user_prompt = PromptManager.get_text2sql_evaluation_user_prompt(
        query=state["user_query"],
        metadata=metadata_str,
        sql_query=state["sql_query"],
        execution_result=execution_result_str,
    )

    result = evaluator.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    )
    output = (
        SQLEvaluation.model_validate(result)
        if not isinstance(result, SQLEvaluation)
        else result
    )

    return {
        "sql_query_status": output.verdict,
        "sql_query_fix": output.fix,
    }


def route_sql_query(state: State):
    """Route the SQL query to the appropriate agent"""
    if state["sql_query_status"] == "correct":
        return "correct"
    elif state["sql_query_status"] == "incorrect":
        return "incorrect"
    else:
        raise ValueError(f"Invalid SQL query status: {state['sql_query_status']}")


# ------------------------------------------------------------
# Graph
# ------------------------------------------------------------


def create_text2sql_subgraph(entry_point_name=START, exit_point_name=END) -> StateGraph:
    """Create a reusable text-to-SQL subgraph

    Args:
        entry_point_name: Name for the subgraph entry point
        exit_point_name: Name for the subgraph exit point

    Returns:
        The text-to-SQL subgraph that can be integrated into larger workflows
    """
    workflow = StateGraph(State)

    # Add nodes
    workflow.add_node("validate_query_llm_call", validate_query_llm_call)
    workflow.add_node("ask_clarification", ask_clarification)
    workflow.add_node("generate_sql_query_llm_call", generate_sql_query_llm_call)
    workflow.add_node("evaluate_sql_query_llm_call", evaluate_sql_query_llm_call)

    # Define edges
    workflow.add_edge(entry_point_name, "validate_query_llm_call")
    workflow.add_conditional_edges(
        "validate_query_llm_call",
        route_validation,
        {
            "valid": "generate_sql_query_llm_call",
            "invalid": exit_point_name,
            "requires_clarification": "ask_clarification",
        },
    )
    workflow.add_edge("ask_clarification", "validate_query_llm_call")
    workflow.add_edge("generate_sql_query_llm_call", "evaluate_sql_query_llm_call")
    workflow.add_conditional_edges(
        "evaluate_sql_query_llm_call",
        route_sql_query,
        {
            "correct": exit_point_name,
            "incorrect": "generate_sql_query_llm_call",
        },
    )

    return workflow


def visualize_graph(graph, filename="workflow_graph.png"):
    """Generate and display the workflow graph visualization"""
    # Create output directory if it doesn't exist
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # Save the graph as PNG
    graph_path = output_dir / filename

    # Check if it's a compiled graph or a StateGraph
    if hasattr(graph, "get_graph"):
        graph_image = graph.get_graph().draw_mermaid_png()
    else:
        # For non-compiled StateGraph
        graph_image = graph.draw_mermaid_png()

    with open(graph_path, "wb") as f:
        f.write(graph_image)

    # Open the image in the default viewer
    abs_path = os.path.abspath(graph_path)
    print(f"Graph visualization saved to: {abs_path}")
    webbrowser.open(f"file://{abs_path}")


def create_main_workflow():
    text2sql_graph = create_text2sql_subgraph(START, END).compile()
    visualize_graph(text2sql_graph, "text2sql_graph.png")

    state = text2sql_graph.invoke(
        {
            "user_query": "Show me all bookings where the total amount exceeds X",
            "connector": DatabaseConnector(),
        }
    )

    pprint(state)


if __name__ == "__main__":
    create_main_workflow()
