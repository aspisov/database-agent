from pathlib import Path
from typing import Any, cast

import frontmatter
from jinja2 import (
    Environment,
    FileSystemLoader,
    StrictUndefined,
    Template,
    TemplateError,
    meta,
)


class PromptManager:
    """
    Manages prompt templates for all agents in the system.
    
    Handles loading, rendering, and providing access to Jinja2 templates
    with frontmatter metadata. Supports various prompt types for different
    agent functions.
    """
    
    _env: Environment | None = None

    @classmethod
    def get_env(cls, templates_dir: str = "prompts/templates") -> Environment:
        """Initialize and return the Jinja2 environment."""
        if cls._env is None:
            cls._env = Environment(
                loader=FileSystemLoader(
                    Path(__file__).parent.parent / templates_dir
                ),
                undefined=StrictUndefined,
            )
        return cls._env

    @staticmethod
    def get_prompt(template: str, **kwargs) -> str:
        """
        Render a prompt template with variables.

        Args:
            template: Template name (without .j2 extension)
            **kwargs: Variables to pass to the template

        Returns:
            Rendered prompt text
        """
        env = PromptManager.get_env()
        if not env or not env.loader:
            raise ValueError("Jinja2 environment or loader not initialized")
            
        template_path = f"{template}.j2"
        try:
            # Get source tuple (source, filename, uptodate)
            source_tuple = env.loader.get_source(env, template_path)
            if source_tuple and len(source_tuple) > 1:
                filename = cast(str, source_tuple[1])
                with open(filename) as file:
                    post = frontmatter.load(file)

                jinja_template: Template = env.from_string(post.content)
                try:
                    return jinja_template.render(**kwargs)
                except TemplateError as e:
                    raise ValueError(
                        f"Error rendering template {template}: {e}"
                    )
            else:
                raise ValueError(
                    f"Template {template} not found or invalid source tuple"
                )
        except Exception as e:
            raise ValueError(f"Error loading template {template}: {e}")

    @staticmethod
    def get_template_info(template: str) -> dict[str, Any]:
        """
        Get metadata about a template.

        Args:
            template: Template name (without .j2 extension)

        Returns:
            Dictionary with template metadata and variables
        """
        env = PromptManager.get_env()
        if not env or not env.loader:
            raise ValueError("Jinja2 environment or loader not initialized")
            
        template_path = f"{template}.j2"
        try:
            # Get source tuple (source, filename, uptodate)
            source_tuple = env.loader.get_source(env, template_path)
            if source_tuple and len(source_tuple) > 1:
                filename = cast(str, source_tuple[1])
                with open(filename) as file:
                    post = frontmatter.load(file)

                ast = env.parse(post.content)
                variables = meta.find_undeclared_variables(ast)

                return {
                    "name": template,
                    "description": post.metadata.get(
                        "description", "No description provided"
                    ),
                    "author": post.metadata.get("author", "Unknown"),
                    "variables": list(variables),
                    "frontmatter": post.metadata,
                }
            else:
                raise ValueError(
                    f"Template {template} not found or invalid source tuple"
                )
        except Exception as e:
            raise ValueError(f"Error loading template info for {template}: {e}")

    # ------ CHAT PROMPTS ------
    @classmethod
    def get_chat_system_prompt(cls, db_info: str | None = None) -> str:
        """Get system prompt for the chat agent."""
        return cls.get_prompt("chat_system", db_info=db_info)

    # ------ ROUTER PROMPTS ------
    @classmethod
    def get_router_system_prompt(cls, examples: bool = True) -> str:
        """Get system prompt for the query router."""
        return cls.get_prompt("router_system", examples=examples)

    @classmethod
    def get_router_user_prompt(cls, query: str, history: str) -> str:
        """Get user prompt for query classification."""
        return cls.get_prompt("router_user", query=query, history=history)

    # ------ TEXT2SQL PROMPTS ------
    @classmethod
    def get_text2sql_generation_system_prompt(
        cls, additional_info: str | None = None
    ) -> str:
        """Get system prompt for SQL generation."""
        return cls.get_prompt(
            "text2sql_generation_system", additional_info=additional_info
        )

    @classmethod
    def get_text2sql_generation_user_prompt(
        cls, query: str, metadata: str
    ) -> str:
        """Get user prompt for SQL generation."""
        return cls.get_prompt(
            "text2sql_generation_user", query=query, metadata=metadata
        )

    @classmethod
    def get_text2sql_verify_prompt(cls) -> str:
        """Get system prompt for SQL query verification."""
        return cls.get_prompt("text2sql_verify")

    @classmethod
    def get_text2sql_verify_user_prompt(cls, query: str, metadata: str) -> str:
        """Get user prompt for SQL query verification."""
        return cls.get_prompt(
            "text2sql_verify_user", query=query, metadata=metadata
        )

    # ------ VISUALIZATION PROMPTS ------
    @classmethod
    def get_modify_query_system_prompt(cls, examples: bool = True) -> str:
        """Get system prompt for visualization query modification."""
        return cls.get_prompt("modify_query_system", examples=examples)
