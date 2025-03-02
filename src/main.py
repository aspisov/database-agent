"""
Main module for the Conversational Database Agent.

This module contains the main entry point for the agent application.
"""

import logging
import json

from src.agents.router import QueryRouter
from src.agents.chat import ChatAgent, MockContext
from src.models.response import (
    AgentResponse,
    Text2SQLResponse,
    VisualizationResponse,
    ChatResponse,
)


def setup_logging() -> None:
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def format_response(response: AgentResponse) -> str:
    """
    Format an agent response for display to the user.

    Args:
        response: The agent response to format.

    Returns:
        A formatted string representation of the response.
    """
    if not response.success:
        return f"⚠️ Error: {response.error}"

    if response.query_type == "Text2SQL":
        # Cast to the specific response type
        text2sql_response = (
            response if isinstance(response, Text2SQLResponse) else None
        )
        sql_query = getattr(
            text2sql_response, "sql_query", "No SQL query available"
        )
        return (
            f"🔍 SQL Query:\n"
            f"{sql_query}\n\n"
            f"💡 Explanation: {response.message}"
        )
    elif response.query_type == "Visualization":
        # Cast to the specific response type
        viz_response = (
            response if isinstance(response, VisualizationResponse) else None
        )
        viz_type = getattr(viz_response, "visualization_type", "unknown")
        return (
            f"📊 Visualization ({viz_type}):\n"
            f"{response.message}\n"
            f"[Visualization would be displayed here in a real UI]"
        )
    else:  # Chat
        # Cast to the specific response type
        chat_response = response if isinstance(response, ChatResponse) else None
        answer = getattr(chat_response, "answer", response.message)
        return f"💬 {answer}"


def main() -> None:
    """Main entry point for the application."""
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Conversational Database Agent")

    # Create a mock context for testing
    context = MockContext()

    # Initialize the router
    router = QueryRouter()

    print("=" * 50)
    print("🤖 Conversational Database Agent")
    print("Type 'exit' or 'quit' to end the session")
    print("=" * 50)

    while True:
        # Get user input
        user_query = input("\n🧑‍💻 Enter your query: ")

        # Check for exit command
        if user_query.lower() in ["exit", "quit", "q"]:
            print("👋 Goodbye!")
            break

        # Route the query and get response
        try:
            response = router.route_query(user_query, context)
            print("\n" + format_response(response))

            # For debugging
            logger.debug(
                f"Response details: {json.dumps(response.dict(), indent=2, default=str)}"
            )

        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            print(f"⚠️ Something went wrong: {str(e)}")


if __name__ == "__main__":
    main()
