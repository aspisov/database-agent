import logging
import operator
import os
import webbrowser
from pathlib import Path
from pprint import pprint
from typing import Any, Dict, Literal

from dotenv import load_dotenv
from IPython.display import Image, display
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph
from pydantic import BaseModel, Field
from typing_extensions import Annotated, TypedDict

from app.database.connector import DatabaseConnector
from app.prompts.prompt_manager import PromptManager

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("text2sql_agent.log"), logging.StreamHandler()],
)
logger = logging.getLogger("text2sql_agent")

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
    errors: Dict[str, str] | None  # Store any errors that occur during processing
    retry_count: int | None  # Track number of retry attempts


def validate_query_llm_call(state: State):
    """Validate the user query"""
    try:
        system_prompt = PromptManager.get_text2sql_validation_system_prompt()

        context: dict[str, Any] = state["connector"].get_text2sql_context()
        metadata_str = str(context) if isinstance(context, dict) else context

        user_prompt = PromptManager.get_text2sql_validation_user_prompt(
            query=state["user_query"], metadata=metadata_str
        )

        logger.info(f"Validating query: {state['user_query'][:50]}...")
        result = validator.invoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        )
        output = (
            QueryValidation.model_validate(result)
            if not isinstance(result, QueryValidation)
            else result
        )

        logger.info(f"Validation result: {output.status}")
        return {
            "user_query_status": output.status,
            "user_query_clarification_question": output.clarification_question,
        }
    except Exception as e:
        logger.error(f"Error validating query: {str(e)}", exc_info=True)
        return {
            "user_query_status": "invalid",
            "errors": {"validation_error": str(e)},
        }


def route_validation(state: State):
    """Route the user query to the appropriate agent"""
    # Check for errors
    if state.get("errors"):
        logger.warning(f"Routing to END due to errors: {state.get('errors')}")
        return "invalid"

    if state["user_query_status"] == "valid":
        return "valid"
    elif state["user_query_status"] == "invalid":
        return "invalid"
    elif state["user_query_status"] == "requires_clarification":
        return "requires_clarification"


def ask_clarification(state: State):
    """Ask the user for clarification"""
    try:
        print(state["user_query_clarification_question"])
        user_query = input("> ")
        updated_user_query = (
            state["user_query"]
            + "\n"
            + f"<Clarification question> {state['user_query_clarification_question']}"
            + "\n"
            + user_query
        )

        logger.info(f"Received clarification: {user_query[:50]}...")
        return {"user_query": updated_user_query}
    except Exception as e:
        logger.error(f"Error in clarification: {str(e)}", exc_info=True)
        return {
            "errors": {"clarification_error": str(e)},
        }


def generate_sql_query_llm_call(state: State):
    """Generate a SQL query from the user query"""
    try:
        system_prompt = PromptManager.get_text2sql_generation_system_prompt()

        context: dict[str, Any] = state["connector"].get_text2sql_context()
        metadata_str = str(context) if isinstance(context, dict) else context

        user_prompt = PromptManager.get_text2sql_generation_user_prompt(
            query=state["user_query"],
            metadata=metadata_str,
            sql_query=state.get("sql_query", ""),
            fix=state.get("sql_query_fix", ""),
        )

        logger.info(f"Generating SQL for query: {state['user_query'][:50]}...")
        result = sql_generator.invoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        )
        output = (
            SQLQuery.model_validate(result)
            if not isinstance(result, SQLQuery)
            else result
        )

        logger.info(f"Generated SQL query: {output.sql_query[:50]}...")
        return {"sql_query": output.sql_query}
    except Exception as e:
        logger.error(f"Error generating SQL query: {str(e)}", exc_info=True)
        return {
            "errors": {"sql_generation_error": str(e)},
        }


def evaluate_sql_query_llm_call(state: State):
    """Evaluate the SQL query"""
    try:
        if state["sql_query"] is None:
            raise ValueError("SQL query cannot be None when evaluating")

        connector = DatabaseConnector()
        logger.info(f"Executing SQL query: {state['sql_query'][:50]}...")
        execution_result = connector.execute_query(state["sql_query"])

        # Display execution results to the user
        print("\n=== SQL Query Results ===")
        print(f"Query: {state['sql_query']}")
        print("\nResults:")
        if isinstance(execution_result, dict):
            import json

            print(json.dumps(execution_result, indent=2))
        else:
            print(execution_result)
        print("==========================\n")

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

        logger.info("Evaluating SQL query...")
        result = evaluator.invoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        )
        output = (
            SQLEvaluation.model_validate(result)
            if not isinstance(result, SQLEvaluation)
            else result
        )

        logger.info(f"Evaluation result: {output.verdict}")

        if output.verdict == "incorrect":
            print("\n⚠️ The query may need improvement. Working on refining it...")
            if output.fix:
                print(f"Suggested fix: {output.fix}\n")
        else:
            print("✓ The query appears to be correct!\n")

        return {
            "sql_query_status": output.verdict,
            "sql_query_fix": output.fix,
        }
    except Exception as e:
        logger.error(f"Error evaluating SQL query: {str(e)}", exc_info=True)
        print(f"\n❌ Error executing SQL query: {str(e)}\n")
        return {
            "sql_query_status": "incorrect",
            "sql_query_fix": f"Error during evaluation: {str(e)}",
            "errors": {"sql_evaluation_error": str(e)},
        }


def route_sql_query(state: State):
    """Route the SQL query to the appropriate agent"""
    # Check for errors
    if state.get("errors"):
        logger.warning(f"Routing to END due to errors: {state.get('errors')}")
        return "incorrect"

    # Check retry count to avoid infinite loops
    retry_count = state.get("retry_count", 0)
    if retry_count is not None and retry_count >= 3:
        logger.warning(
            f"Maximum retry attempts reached ({retry_count}). Ending workflow."
        )
        return "max_retries"

    if state["sql_query_status"] == "correct":
        return "correct"
    elif state["sql_query_status"] == "incorrect":
        # Increment retry count
        return "incorrect"
    else:
        logger.error(f"Invalid SQL query status: {state['sql_query_status']}")
        return "incorrect"


def increment_retry_count(state: State):
    """Increment the retry counter"""
    current_count = state.get("retry_count", 0)
    if current_count is None:
        current_count = 0

    logger.info(f"Incrementing retry count from {current_count} to {current_count + 1}")
    return {"retry_count": current_count + 1}


# ------------------------------------------------------------
# Graph
# ------------------------------------------------------------


def create_text2sql_subgraph(
    entry_point_name: str | None = None, exit_point_name: str | None = None
):
    """Create a reusable text-to-SQL subgraph

    Args:
        entry_point_name: Deprecated, not used
        exit_point_name: Deprecated, not used

    Returns:
        The text-to-SQL subgraph that can be integrated into larger workflows
    """
    workflow = StateGraph(State)

    # Add nodes
    workflow.add_node("validate_query_llm_call", validate_query_llm_call)
    workflow.add_node("ask_clarification", ask_clarification)
    workflow.add_node("generate_sql_query_llm_call", generate_sql_query_llm_call)
    workflow.add_node("evaluate_sql_query_llm_call", evaluate_sql_query_llm_call)
    workflow.add_node("increment_retry_count", increment_retry_count)

    # Initialize the workflow with retry_count of 0
    def init_workflow(state: State):
        """Initialize workflow state with default values"""
        return {"retry_count": 0}

    workflow.add_node("init", init_workflow)

    # Define edges - using START and END for the entry and exit points
    workflow.add_edge(START, "init")
    workflow.add_edge("init", "validate_query_llm_call")
    workflow.add_conditional_edges(
        "validate_query_llm_call",
        route_validation,
        {
            "valid": "generate_sql_query_llm_call",
            "invalid": END,
            "requires_clarification": "ask_clarification",
        },
    )
    workflow.add_edge("ask_clarification", "validate_query_llm_call")
    workflow.add_edge("generate_sql_query_llm_call", "evaluate_sql_query_llm_call")
    workflow.add_conditional_edges(
        "evaluate_sql_query_llm_call",
        route_sql_query,
        {
            "correct": END,
            "incorrect": "increment_retry_count",
            "max_retries": END,
        },
    )
    workflow.add_edge("increment_retry_count", "generate_sql_query_llm_call")

    logger.info("Text2SQL subgraph created successfully")
    return workflow


def create_main_workflow():
    text2sql_graph = create_text2sql_subgraph().compile()

    state = text2sql_graph.invoke(
        {
            "user_query": "Show me all bookings where the total amount exceeds X",
            "connector": DatabaseConnector(),
        }
    )

    pprint(state)


if __name__ == "__main__":
    create_main_workflow()
