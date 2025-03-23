import logging
import os
import webbrowser
from pathlib import Path
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph
from pydantic import BaseModel, Field

from app.agents.text2sql import create_text2sql_subgraph
from app.database.connector import DatabaseConnector
from app.prompts.prompt_manager import PromptManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("router_agent.log"), logging.StreamHandler()],
)
logger = logging.getLogger("router_agent")

# ------------------------------------------------------------
# Models
# ------------------------------------------------------------


class QueryClassification(BaseModel):
    """Classification result for user queries"""

    query_type: Literal["Text2SQL", "Chat"] = Field(description="The type of query")
    updated_query: str | None = Field(
        default=None,
        description="Updated query based on conversation context when clarifying previous queries",
    )


class ChatResponse(BaseModel):
    """Response from the chat agent"""

    response: str = Field(description="The response to the user's query")


llm = ChatOpenAI(model="gpt-4o-mini")
router = llm.with_structured_output(QueryClassification)
chat_agent = llm.with_structured_output(ChatResponse)


# ------------------------------------------------------------
# Workflow
# ------------------------------------------------------------


class State(MessagesState):
    user_query: str
    summary: str
    query_type: Literal["Text2SQL", "Chat"]
    connector: DatabaseConnector


def router_llm_call(state: State):
    """
    Routes user queries to the appropriate agent (Text2SQL or Chat)
    """
    system_prompt = PromptManager.get_router_system_prompt()

    # Get the last message if available
    user_message = state["user_query"]

    user_prompt = PromptManager.get_router_user_prompt(
        query=user_message,
    )

    logger.info(f"Routing query: {user_message[:50]}...")
    output = router.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    )

    # Ensure output is properly typed
    query_result = (
        QueryClassification.model_validate(output)
        if not isinstance(output, QueryClassification)
        else output
    )

    # If there's an updated query, use it
    updated_query = (
        query_result.updated_query if query_result.updated_query else user_message
    )

    logger.info(f"Query classified as: {query_result.query_type}")
    return {
        "query_type": query_result.query_type,
        "user_query": updated_query,
    }


def route_query(state: State):
    if state["query_type"] == "Text2SQL":
        return "text2sql"
    else:
        return "chat"


def chat_agent_call(state: State):
    """
    Handle general chat queries about the database
    """
    try:
        system_prompt = PromptManager.get_chat_system_prompt(
            db_info=str(state["connector"].get_text2sql_context())
        )

        logger.info(f"Processing chat query: {state['user_query'][:50]}...")
        result = chat_agent.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=state["user_query"]),
            ]
        )

        chat_result = (
            ChatResponse.model_validate(result)
            if not isinstance(result, ChatResponse)
            else result
        )
        logger.info("Chat response generated successfully")

        # Return the response
        print(chat_result.response)
        return {}
    except Exception as e:
        logger.error(f"Error in chat agent: {str(e)}", exc_info=True)
        print(f"I encountered an error: {str(e)}")
        return {}


def summarize_conversation(state: State):
    """Summarize the conversation history to prevent context overload"""
    system_prompt = "You are an expert conversation summarizer. Summarize the following conversation concisely while preserving all important information."

    conversation_history = str(state["messages"]) if "messages" in state else ""

    summarizer = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    summary = summarizer.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content=f"Summarize this conversation:\n{conversation_history}"
            ),
        ]
    ).content

    logger.info("Conversation summarized")
    # Update the state with the summary
    return {
        "summary": summary,
        # Reset messages to only include the summary as context
        "messages": [
            SystemMessage(content=f"Previous conversation summary: {summary}")
        ],
    }


def should_summarize(state: State):
    if len(state["messages"]) > 5:
        return "summarize"
    return "route"


# ------------------------------------------------------------
# Graph
# ------------------------------------------------------------


router_workflow = StateGraph(State)
router_workflow.add_node("summarizer", summarize_conversation)
router_workflow.add_node("router", router_llm_call)
router_workflow.add_node("chat", chat_agent_call)

# Create the text2sql subgraph with default entry/exit points (START/END)
text2sql_subgraph = create_text2sql_subgraph()
compiled_text2sql = text2sql_subgraph.compile()

# Add the subgraph as a node in the main workflow
router_workflow.add_node("text2sql", compiled_text2sql)

router_workflow.add_conditional_edges(
    START,
    should_summarize,
    {"summarize": "summarizer", "route": "router"},
)
router_workflow.add_edge("summarizer", "router")
router_workflow.add_conditional_edges(
    "router",
    route_query,
    {"text2sql": "text2sql", "chat": "chat"},
)
router_workflow.add_edge("chat", END)
router_workflow.add_edge("text2sql", END)

graph = router_workflow.compile()


def visualize_graph(graph, filename="workflow_graph.png"):
    from langchain_core.runnables.graph_mermaid import MermaidDrawMethod

    """Generate and display the workflow graph visualization"""
    # Create output directory if it doesn't exist
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    try:
        # Save the graph as PNG
        graph_path = output_dir / filename

        graph_image = graph.get_graph(xray=1).draw_mermaid_png(
            draw_method=MermaidDrawMethod.PYPPETEER
        )

        with open(graph_path, "wb") as f:
            f.write(graph_image)

        # Open the image in the default viewer
        abs_path = os.path.abspath(graph_path)
        logger.info(f"Graph visualization saved to: {abs_path}")
        print(f"Graph visualization saved to: {abs_path}")
        webbrowser.open(f"file://{abs_path}")
    except Exception as e:
        logger.error(f"Could not visualize graph: {str(e)}", exc_info=True)
        print(f"Warning: Could not visualize graph due to error: {e}")
        print("Continuing without visualization...")


if __name__ == "__main__":
    visualize_graph(graph)

    # graph.invoke(
    #     {
    #         "user_query": "Show me all bookings where the total amount exceeds X",
    #         "connector": DatabaseConnector(),
    #     }
    # )
