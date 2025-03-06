from typing import Any


class Context:
    def __init__(self):
        # Chat and query history
        self.messages: list[dict[str, Any]] = []  # [{role, content, timestamp}]

    def add_message(
        self, role: str, content: str, query_type: str | None = None
    ) -> dict[str, Any]:
        """Add a message to the history with timestamp"""
        message = {
            "role": role,
            "content": content,
            "query_type": query_type,
            # "timestamp": datetime.now(),
        }
        self.messages.append(message)
        return message

    def get_conversation_history(
        self, max_messages: int = 3
    ) -> list[dict[str, Any]]:
        """Get recent conversation for context"""
        return self.messages[-max_messages:]
