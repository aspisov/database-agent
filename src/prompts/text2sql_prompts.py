# ------------------------------------------------------------------------------
# Generation prompts
# ------------------------------------------------------------------------------

TEXT2SQL_GENERATION_SYSTEM_PROMPT = """
You are a PostgreSQL expert. Your goal is to convert natural language queries into SQL queries.
You will be given a user query and database metadata.

Use chain-of-thought reasoning before generating the final SQL query.
"""

TEXT2SQL_GENERATION_USER_PROMPT = """
User Query: {query}

Database Metadata: {metadata}
"""

# ------------------------------------------------------------------------------
# Verification prompts
# ------------------------------------------------------------------------------

TEXT2SQL_VERIFY_PROMPT = """
You are a PostgreSQL expert. Your task is to determine whether the user query:
- is valid (can be answered with the given database metadata),
- requires clarification (the query is ambiguous or incomplete), or
- is invalid (unrelated to this database).

Please explain your reasoning step by step before reaching a conclusion.
"""

TEXT2SQL_VERIFY_USER_PROMPT = """
User Query: {query}

Database Metadata: {metadata}

Use chain-of-thought reasoning to assess the query and then provide your verdict.
"""
