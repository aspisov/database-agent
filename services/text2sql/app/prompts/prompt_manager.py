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
                loader=FileSystemLoader(Path(__file__).parent.parent / templates_dir),
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
                    raise ValueError(f"Error rendering template {template}: {e}")
            else:
                raise ValueError(
                    f"Template {template} not found or invalid source tuple"
                )
        except Exception as e:
            raise ValueError(f"Error loading template {template}: {e}")

    @classmethod
    def get_generation_system_prompt(cls) -> str:
        """Get system prompt for SQL generation."""
        return cls.get_prompt("generation_system")

    @classmethod
    def get_generation_user_prompt(
        cls,
        user_query: str,
        metadata: str,
        sql_query: str | None = None,
        correction: str | None = None,
    ) -> str:
        """Get user prompt for SQL generation."""
        return cls.get_prompt(
            "generation_user",
            user_query=user_query,
            metadata=metadata,
            sql_query=sql_query,
            correction=correction,
        )

    @classmethod
    def get_validation_system_prompt(cls) -> str:
        """Get system prompt for SQL query validation."""
        return cls.get_prompt("validation_system")

    @classmethod
    def get_validation_user_prompt(cls, user_query: str, metadata: str) -> str:
        """Get user prompt for SQL query validation."""
        return cls.get_prompt("validation_user", user_query=user_query, metadata=metadata)

    @classmethod
    def get_evaluation_system_prompt(cls) -> str:
        """Get system prompt for SQL query evaluation."""
        return cls.get_prompt("evaluation_system")

    @classmethod
    def get_evaluation_user_prompt(
        cls, user_query: str, metadata: str, sql_query: str, execution_results: str
    ) -> str:
        """Get user prompt for SQL query evaluation."""
        return cls.get_prompt(
            "evaluation_user",
            user_query=user_query,
            metadata=metadata,
            sql_query=sql_query,
            execution_results=execution_results,
        )

    @classmethod
    def get_response_system_prompt(cls) -> str:
        """Get system prompt for response formatting."""
        return cls.get_prompt("response_system")

    @classmethod
    def get_response_user_prompt(
        cls, user_query: str, metadata: str, sql_query: str, execution_results: str
    ) -> str:
        """Get user prompt for response formatting."""
        return cls.get_prompt(
            "response_user",
            user_query=user_query,
            metadata=metadata,
            sql_query=sql_query,
            execution_results=execution_results,
        )
