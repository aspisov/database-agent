from datetime import datetime
import typing as tp

import pandas as pd


class Context:
    def __init__(self):
        # Chat and query history
        self.messages = []  # [{role, content, timestamp}]

        # Current working data
        self.current_dataframe = None  # Most recent query result as DataFrame
        self.current_sql = None  # Most recent SQL query
        self.current_table_context = (
            None  # Tables relevant to current conversation
        )

        # Database metadata (lazy-loaded)
        self._schema_cache = {}  # {table_name: column_info}
        self._table_samples = {}  # {table_name: sample_rows}

        # Error handling
        self.query_errors = []  # Recent SQL errors for correction

    def add_message(self, role: str, content: str) -> dict[str, tp.Any]:
        """Add a message to the history with timestamp"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(),
        }
        self.messages.append(message)
        return message

    def get_conversation_history(
        self, max_messages: int = 5
    ) -> list[dict[str, tp.Any]]:
        """Get recent conversation for context"""
        return self.messages[-max_messages:]

    def update_current_dataframe(self, df: pd.DataFrame) -> None:
        """Update the current working dataframe"""
        self.current_dataframe = df

    def update_current_sql(self, sql: str) -> None:
        """Update the current working SQL query"""
        self.current_sql = sql
