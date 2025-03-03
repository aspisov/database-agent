"""
Streamlit web interface for the Conversational Database Agent.

This module provides a web-based GUI using Streamlit to interact with the
Conversational Database Agent.
"""

import streamlit as st
import pandas as pd
import altair as alt
import logging

from src.agents.router import QueryRouter
from src.models.response import (
    AgentResponse,
    Text2SQLResponse,
    VisualizationResponse,
    ChatResponse,
)
from src.utils.dataframe_utils import query_results_to_dataframe

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Set page config
st.set_page_config(
    page_title="Database Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


def display_response(response: AgentResponse) -> None:
    """
    Display an agent response in the Streamlit interface.

    Args:
        response: The agent response to display.
    """
    if not response.success:
        st.error(f"Error: {response.error}")
        return

    if response.query_type == "Text2SQL":
        # Cast to the specific response type
        text2sql_response = (
            response if isinstance(response, Text2SQLResponse) else None
        )
        sql_query = getattr(
            text2sql_response, "sql_query", "No SQL query available"
        )
        query_results = getattr(text2sql_response, "query_results", None)

        with st.expander("SQL Query", expanded=True):
            st.code(sql_query, language="sql")

        df = query_results_to_dataframe(query_results)
        if df is not None:
            st.subheader("Results")
            st.dataframe(df)

            # Add download button for CSV
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download data as CSV",
                data=csv,
                file_name="query_results.csv",
                mime="text/csv",
            )

        st.success(f"Explanation: {response.message}")

    else:  # Chat
        chat_response = response if isinstance(response, ChatResponse) else None
        answer = getattr(chat_response, "answer", response.message)
        st.info(answer)


def main():
    """Main function for the Streamlit app."""
    # Initialize the router
    router = QueryRouter()

    # Sidebar
    with st.sidebar:
        st.title("🤖 Database Agent")
        st.markdown("---")
        st.markdown(
            """
            This application allows you to interact with your database using natural language.
            
            You can:
            
            - Ask questions about your data
            - Request SQL queries to be generated
            - Get visualizations of your data
            - Chat with the agent about your database
            """
        )
        st.markdown("---")

        # Additional controls could go here
        st.markdown("### Options")

        # Example: Toggle for showing SQL queries
        # show_sql = st.checkbox("Always show SQL queries", value=True)

    # Main area
    st.title("Conversational Database Agent")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.markdown(message["content"])
            else:  # assistant
                if isinstance(message["content"], AgentResponse):
                    display_response(message["content"])
                else:
                    st.markdown(message["content"])

    # Input area
    if prompt := st.chat_input("What would you like to know about your data?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Get response from the agent
                    response = router.route_query(prompt)

                    # Display the response
                    display_response(response)

                    # Add assistant response to chat history
                    st.session_state.messages.append(
                        {"role": "assistant", "content": response}
                    )

                except Exception as e:
                    logger.error(f"Error processing query: {e}", exc_info=True)
                    st.error(f"Something went wrong: {str(e)}")
                    # Add error message to chat history
                    st.session_state.messages.append(
                        {"role": "assistant", "content": f"Error: {str(e)}"}
                    )


if __name__ == "__main__":
    main()
