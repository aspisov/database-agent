"""
Database Connector Module

This module provides a connector to interact with PostgreSQL databases.
"""

import logging
import typing as tp

import pandas as pd
from config.settings import get_settings
from sqlalchemy import (
    MetaData,
    Table,
    create_engine,
    func,
    inspect,
    select,
    text,
)
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker


class DatabaseConnector:
    """Connector for PostgreSQL database interactions."""

    def __init__(self):
        """
        Initialize the database connector.

        Args:
            host: Database host
            port: Database port
            dbname: Database name
            user: Database user
            password: Database password
            schema: Database schema
        """
        self.settings = get_settings()
        self.host = self.settings.database.host
        self.port = self.settings.database.port
        self.db_name = self.settings.database.db_name
        self.user = self.settings.database.user
        self.password = self.settings.database.password
        self.schema_name = self.settings.database.schema_name
        self.logger = logging.getLogger(__name__)

        # SQLAlchemy components
        self._engine = None
        self._metadata = None
        self._inspector = None
        self._session_factory = None
        self._connection = None

        # Initialize on creation
        self._initialize()

    def _initialize(self):
        """Initialize SQLAlchemy components"""
        self._engine = self._get_connection()
        self._metadata = MetaData(schema=self.schema_name)
        self._metadata.reflect(bind=self._engine)
        self._inspector = inspect(self._engine)
        self._session_factory = sessionmaker(bind=self._engine)

    def _get_connection(self) -> Engine:
        """
        Get a database connection.

        Returns:
            SQLAlchemy Engine object

        Raises:
            Exception: If connection fails
        """
        try:
            if self._engine is None:
                self.logger.info(
                    f"Connecting to PostgreSQL database {self.db_name} on {self.host}:{self.port}"
                )
                connection_string = f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db_name}"
                self._engine = create_engine(
                    connection_string,
                    pool_pre_ping=True,
                    pool_recycle=3600,
                )
            return self._engine
        except Exception as e:
            self.logger.error(f"Failed to connect to database: {str(e)}")
            raise

    def get_session(self) -> Session:
        """Get a new SQLAlchemy session"""
        if self._session_factory is None:
            self._initialize()
        return self._session_factory()

    def close(self):
        """Close the database connection."""
        if self._engine:
            self._engine.dispose()
            self._engine = None
            self.logger.info("Database connection closed")

    def test_connection(self) -> bool:
        """
        Test the database connection.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            return False

    def execute_query(
        self,
        query: str,
        params: dict[str, tp.Any] | None = None,
        timeout: int | None = None,
    ) -> dict[str, tp.Any]:
        """
        Execute a SQL query and return the results.

        Args:
            query: SQL query to execute
            params: Query parameters
            timeout: Query timeout in seconds

        Returns:
            Dictionary with query results and metadata
        """
        try:
            with self._engine.connect() as conn:
                if timeout:
                    conn = conn.execution_options(timeout=timeout)

                result_proxy = conn.execute(text(query), params or {})

                if result_proxy.returns_rows:
                    # Get column names
                    columns = result_proxy.keys()

                    # Fetch all rows
                    rows = [
                        dict(zip(columns, row))
                        for row in result_proxy.fetchall()
                    ]

                    return {
                        "success": True,
                        "columns": columns,
                        "rows": rows,
                        "row_count": len(rows),
                        "query": query,
                    }
                else:
                    # For INSERT, UPDATE, DELETE operations
                    return {
                        "success": True,
                        "row_count": result_proxy.rowcount,
                        "query": query,
                    }
        except Exception as e:
            self.logger.error(f"Query execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "query": query,
            }

    def get_schema_info(self) -> dict[str, tp.Any]:
        """
        Get comprehensive database schema information.

        Returns:
            Dictionary with complete schema information
        """
        schema_info = {
            "tables": [],
            "relationships": self.get_table_relationships(),
            "database_name": self.db_name,
            "schema_name": self.schema_name,
        }

        # Get all tables
        tables = self.get_tables()

        for table_name in tables:
            # Get table comment
            table_comment = None
            try:
                comment_info = self._inspector.get_table_comment(
                    table_name, schema=self.schema_name
                )
                if comment_info and "text" in comment_info:
                    table_comment = comment_info["text"]
            except (NotImplementedError, Exception) as e:
                self.logger.debug(
                    f"Could not retrieve comment for table {table_name}: {str(e)}"
                )

            table_info = {
                "name": table_name,
                "columns": [],
                "primary_keys": self._inspector.get_pk_constraint(
                    table_name, schema=self.schema_name
                )["constrained_columns"],
                "indexes": self._inspector.get_indexes(
                    table_name, schema=self.schema_name
                ),
                "sample_data": self.get_sample_data(table_name, 3),
                "row_count": self.get_row_count(table_name),
                "comment": table_comment,
            }

            # Get column information
            for column in self._inspector.get_columns(
                table_name, schema=self.schema_name
            ):
                column_info = {
                    "name": column["name"],
                    "type": str(column["type"]),
                    "nullable": column["nullable"],
                    "default": (
                        str(column["default"])
                        if column["default"] is not None
                        else None
                    ),
                    "comment": column.get("comment"),
                }

                # Check if column is part of primary key
                if column["name"] in table_info["primary_keys"]:
                    column_info["is_primary_key"] = True

                # Add to columns list
                table_info["columns"].append(column_info)

            # Add table info to schema
            schema_info["tables"].append(table_info)

        return schema_info

    def get_table_relationships(self) -> list[dict[str, str]]:
        """
        Get foreign key relationships between tables.

        Returns:
            List of dictionaries with relationship information
        """
        relationships = []

        for table_name in self.get_tables():
            for fk in self._inspector.get_foreign_keys(
                table_name, schema=self.schema_name
            ):
                relationship = {
                    "source_table": table_name,
                    "source_column": fk["constrained_columns"][0],
                    "target_table": fk["referred_table"],
                    "target_column": fk["referred_columns"][0],
                    "constraint_name": fk.get("name", ""),
                }
                relationships.append(relationship)

        return relationships

    def get_tables(self) -> list[str]:
        """
        Get list of all tables in the database.

        Returns:
            List of table names
        """
        return self._inspector.get_table_names(schema=self.schema_name)

    def get_sample_data(
        self, table_name: str, limit: int = 5
    ) -> list[dict[str, tp.Any]]:
        """
        Get sample data from a table.

        Args:
            table_name: Name of the table
            limit: Maximum number of rows to return

        Returns:
            List of dictionaries with sample data
        """
        try:
            query = (
                f"SELECT * FROM {self.schema_name}.{table_name} LIMIT {limit}"
            )
            result = self.execute_query(query)
            return result.get("rows", [])
        except Exception as e:
            self.logger.error(
                f"Failed to get sample data for {table_name}: {str(e)}"
            )
            return []

    def get_row_count(self, table_name: str) -> int:
        """
        Get the number of rows in a table.

        Args:
            table_name: Name of the table

        Returns:
            Number of rows
        """
        try:
            table = Table(
                table_name, self._metadata, autoload_with=self._engine
            )
            with self._engine.connect() as conn:
                count_query = select(func.count()).select_from(table)
                result = conn.execute(count_query)
                return result.scalar()
        except Exception as e:
            self.logger.error(
                f"Failed to get row count for {table_name}: {str(e)}"
            )
            return -1

    def get_text2sql_context(self) -> dict[str, tp.Any]:
        """
        Get comprehensive context information for text-to-SQL operations.

        Returns:
            Dictionary with schema and sample data information formatted
            specifically for text-to-SQL models
        """
        schema_info = self.get_schema_info()

        # Format tables information in a text-to-SQL friendly way
        tables_info = []
        for table in schema_info["tables"]:
            table_desc = [
                f"Table: {table['name']}",
            ]

            # Add table comment if available
            if table.get("comment"):
                table_desc.append(f"Description: {table['comment']}")

            table_desc.append(f"Columns:")

            for col in table["columns"]:
                pk_marker = "PK" if col.get("is_primary_key") else ""
                nullable = "NULL" if col["nullable"] else "NOT NULL"
                column_line = (
                    f"  - {col['name']} ({col['type']}) {pk_marker} {nullable}"
                )

                # Add column comment if available
                if col.get("comment"):
                    column_line += f" - {col['comment']}"

                table_desc.append(column_line)

            if table["sample_data"]:
                table_desc.append(
                    f"Sample data ({len(table['sample_data'])} rows):"
                )
                for row in table["sample_data"]:
                    table_desc.append(f"  {row}")

            if table["row_count"] > 0:
                table_desc.append(f"Total rows: {table['row_count']}")

            tables_info.append("\n".join(table_desc))

        # Format relationships
        relationships_info = []
        for rel in schema_info["relationships"]:
            relationships_info.append(
                f"{rel['source_table']}.{rel['source_column']} -> "
                f"{rel['target_table']}.{rel['target_column']}"
            )

        return {
            "database_name": schema_info["database_name"],
            "schema_name": schema_info["schema_name"],
            "tables": tables_info,
            "relationships": relationships_info,
            "sql_dialect": "PostgreSQL",
        }

    def to_dataframe(
        self, query_results: dict[str, tp.Any]
    ) -> pd.DataFrame | None:
        """
        Convert query results to a pandas DataFrame.

        Args:
            query_results: The results from execute_query method

        Returns:
            pandas DataFrame containing the query results or None if conversion fails
        """
        if not query_results.get("success", False):
            self.logger.error(
                f"Cannot convert failed query to DataFrame: {query_results.get('error')}"
            )
            return None

        if "rows" not in query_results:
            self.logger.info(
                "Query did not return any rows to convert to DataFrame"
            )
            return None

        try:
            # Create DataFrame from rows
            df = pd.DataFrame(query_results["rows"])
            return df
        except Exception as e:
            self.logger.error(
                f"Failed to convert query results to DataFrame: {str(e)}"
            )
            return None

    def execute_query_to_df(
        self,
        query: str,
        params: dict[str, tp.Any] | None = None,
        timeout: int | None = None,
    ) -> pd.DataFrame | None:
        """
        Execute a SQL query and return the results as a pandas DataFrame.

        Args:
            query: SQL query to execute
            params: Query parameters
            timeout: Query timeout in seconds

        Returns:
            DataFrame with query results or None if query fails
        """
        results = self.execute_query(query, params, timeout)
        return self.to_dataframe(results)

    def __del__(self):
        """Clean up resources when object is garbage collected."""
        self.close()


if __name__ == "__main__":
    from pprint import pprint

    connector = DatabaseConnector()
    pprint(connector.get_text2sql_context())
