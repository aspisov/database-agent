from typing import Any, Literal

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from app.agents.models import (
    FormattedResponse,
    QueryValidation,
    SQLEvaluation,
    SQLQuery,
)
from app.agents.utils import visualize_graph
from app.database.connector import DatabaseConnector
from app.prompts.prompt_manager import PromptManager

load_dotenv()

# ------------------------------------------------------------
# Models
# ------------------------------------------------------------

connector = DatabaseConnector()

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
validator = llm.with_structured_output(QueryValidation)
sql_generator = llm.with_structured_output(SQLQuery)
evaluator = llm.with_structured_output(SQLEvaluation)
formatter = llm.with_structured_output(FormattedResponse)

# ------------------------------------------------------------
# States
# ------------------------------------------------------------


class State(TypedDict):
    """State for the workflow"""

    user_query: str
    user_query_status: Literal["valid", "invalid"] | None
    user_query_clarification_question: str | None
    sql_query: str | None
    sql_query_status: Literal["correct", "incorrect"] | None
    sql_query_correction: str | None
    execution_results: dict[str, Any] | None


class OutputState(TypedDict):
    """Output state for the workflow"""

    status: Literal["success", "invalid"]
    answer: str


# ------------------------------------------------------------
# Nodes
# ------------------------------------------------------------


def validate_query_llm_call(state: State):
    """Validate the user query"""
    system_prompt = PromptManager.get_validation_system_prompt()

    context: dict[str, Any] = connector.get_text2sql_context()
    metadata_str = str(context) if isinstance(context, dict) else context

    user_prompt = PromptManager.get_validation_user_prompt(
        user_query=state["user_query"], metadata=metadata_str
    )

    response = validator.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    )
    output = (
        QueryValidation.model_validate(response)
        if not isinstance(response, QueryValidation)
        else response
    )

    return {
        "user_query_status": output.status,
        "user_query_clarification_question": output.clarification_question,
    }


def generate_sql_query_llm_call(state: State):
    """Generate a SQL query from the user query"""
    system_prompt = PromptManager.get_generation_system_prompt()

    context: dict[str, Any] = connector.get_text2sql_context()
    metadata_str = str(context) if isinstance(context, dict) else context

    user_prompt = PromptManager.get_generation_user_prompt(
        user_query=state["user_query"],
        metadata=metadata_str,
        sql_query=state.get("sql_query", ""),
        correction=state.get("sql_query_correction", ""),
    )

    response = sql_generator.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    )
    output = (
        SQLQuery.model_validate(response)
        if not isinstance(response, SQLQuery)
        else response
    )

    execution_results = connector.execute_query(output.sql_query)

    return {
        "sql_query": output.sql_query,
        "execution_results": execution_results,
    }


def evaluate_sql_query_llm_call(state: State):
    """Evaluate the SQL query"""
    if state["sql_query"] is None:
        raise ValueError("SQL query cannot be None when evaluating")

    system_prompt = PromptManager.get_evaluation_system_prompt()

    context: dict[str, Any] = connector.get_text2sql_context()
    metadata_str = str(context) if isinstance(context, dict) else context

    user_prompt = PromptManager.get_evaluation_user_prompt(
        user_query=state["user_query"],
        metadata=metadata_str,
        sql_query=state["sql_query"],
        execution_results=str(state["execution_results"]),
    )

    response = evaluator.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    )
    output = (
        SQLEvaluation.model_validate(response)
        if not isinstance(response, SQLEvaluation)
        else response
    )

    return {
        "sql_query_status": output.verdict,
        "sql_query_correction": output.correction,
    }


def format_response_llm_call(state: State):
    """Format the response"""

    if state["user_query_status"] == "invalid":
        return {
            "status": "invalid",
            "answer": (
                state["user_query_clarification_question"]
                if state["user_query_clarification_question"]
                else "I'm sorry, I cannot answer this question."
            ),
        }
    elif not state["sql_query"] or not state["execution_results"]:
        return {
            "status": "invalid",
            "answer": "An error occurred while generating the SQL query.",
        }

    system_prompt = PromptManager.get_response_system_prompt()

    context: dict[str, Any] = connector.get_text2sql_context()
    metadata_str = str(context) if isinstance(context, dict) else context

    user_prompt = PromptManager.get_response_user_prompt(
        user_query=state["user_query"],
        metadata=metadata_str,
        sql_query=state["sql_query"],
        execution_results=str(state["execution_results"]),
    )

    response = formatter.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    )

    response = (
        FormattedResponse.model_validate(response)
        if not isinstance(response, FormattedResponse)
        else response
    )

    return {
        "status": "success",
        "answer": response.answer,
    }


# ------------------------------------------------------------
# Conditional edges
# ------------------------------------------------------------


def route_sql_query(state: State):
    """Route the SQL query to the appropriate agent"""
    if state["sql_query_status"] == "correct":
        return "correct"
    elif state["sql_query_status"] == "incorrect":
        return "incorrect"
    else:
        raise ValueError(f"Invalid SQL query status: {state['sql_query_status']}")


def route_validation(state: State):
    """Route the user query to the appropriate agent"""
    if state["user_query_status"] == "valid":
        return "valid"
    elif state["user_query_status"] == "invalid":
        return "invalid"
    else:
        raise ValueError(f"Invalid user query status: {state['user_query_status']}")


# ------------------------------------------------------------
# Graph
# ------------------------------------------------------------


def create_text2sql_graph(entry_point_name=START, exit_point_name=END) -> StateGraph:
    """Create a reusable text-to-SQL graph

    Args:
        entry_point_name: Name for the graph entry point
        exit_point_name: Name for the graph exit point

    Returns:
        The text-to-SQL graph that can be integrated into larger workflows
    """
    workflow = StateGraph(State, output=OutputState)

    # Add nodes
    workflow.add_node("validate_query_llm_call", validate_query_llm_call)
    workflow.add_node("generate_sql_query_llm_call", generate_sql_query_llm_call)
    workflow.add_node("evaluate_sql_query_llm_call", evaluate_sql_query_llm_call)
    workflow.add_node("format_response_llm_call", format_response_llm_call)

    # Define edges
    workflow.add_edge(entry_point_name, "validate_query_llm_call")
    workflow.add_conditional_edges(
        "validate_query_llm_call",
        route_validation,
        {
            "valid": "generate_sql_query_llm_call",
            "invalid": "format_response_llm_call",
        },
    )
    workflow.add_edge("generate_sql_query_llm_call", "evaluate_sql_query_llm_call")
    workflow.add_conditional_edges(
        "evaluate_sql_query_llm_call",
        route_sql_query,
        {
            "correct": "format_response_llm_call",
            "incorrect": "generate_sql_query_llm_call",
        },
    )
    workflow.add_edge("format_response_llm_call", exit_point_name)
    return workflow


def create_main_workflow():
    text2sql_graph = create_text2sql_graph(START, END).compile()
    visualize_graph(text2sql_graph, "text2sql_graph.png")

    state = text2sql_graph.invoke(
        {
            "user_query": "Show me all bookings where the total amount exceeds 500",
        }
    )

    print(state["answer"])


if __name__ == "__main__":
    create_main_workflow()
