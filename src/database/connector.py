"""
Database Connector Module

This module provides a connector to interact with PostgreSQL databases.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Union

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import connection, cursor
from psycopg2.extras import RealDictCursor

from config.settings import settings


class DatabaseConnector:
    """
    PostgreSQL Database Connector

    Handles connections to PostgreSQL databases and provides methods for
    querying and schema inspection.
    """

    def __init__(
        self,
        host: str,
        port: int,
        dbname: str,
        user: str,
        password: str,
    ):
        """
        Initialize the database connector.

        Args:
            host: Database host
            port: Database port
            dbname: Database name
            user: Database user
            password: Database password
        """
        self.host = host
        self.port = port
        self.dbname = dbname
        self.user = user
        self.password = password
        self.logger = logging.getLogger(__name__)
        self._connection = None

    def _get_connection(self) -> connection:
        """
        Get a database connection.

        Returns:
            psycopg2 connection object

        Raises:
            Exception: If connection fails
        """
        try:
            if self._connection is None or self._connection.closed:
                self.logger.info(
                    f"Connecting to PostgreSQL database {self.dbname} on {self.host}:{self.port}"
                )
                self._connection = psycopg2.connect(
                    host=self.host,
                    port=self.port,
                    dbname=self.dbname,
                    user=self.user,
                    password=self.password,
                )
            return self._connection
        except Exception as e:
            self.logger.error(f"Failed to connect to database: {str(e)}")
            raise

    def close(self):
        """Close the database connection."""
        if self._connection and not self._connection.closed:
            self._connection.close()
            self._connection = None
            self.logger.info("Database connection closed")

    def test_connection(self) -> bool:
        """
        Test the database connection.

        Returns:
            True if connection succeeds, False otherwise
        """
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
            return True
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            return False

    def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Execute an SQL query and return the results.

        Args:
            query: SQL query to execute
            params: Optional parameters for the query
            timeout: Optional timeout in seconds

        Returns:
            Dictionary containing:
                - success: Whether the query executed successfully
                - columns: List of column names (if success)
                - data: List of tuples with row data (if success)
                - error: Error message (if not success)
        """
        self.logger.info(f"Executing query: {query}")

        if timeout is None:
            timeout = settings.SQL_QUERY_TIMEOUT

        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute(query, params or {})

                # If the query is a SELECT, fetch results
                if cur.description:
                    columns = [desc[0] for desc in cur.description]
                    data = cur.fetchall()
                    conn.commit()

                    # Truncate result if too large (for UI display)
                    max_rows = 1000
                    data_truncated = len(data) > max_rows
                    if data_truncated:
                        data = data[:max_rows]

                    return {
                        "success": True,
                        "columns": columns,
                        "data": data,
                        "row_count": cur.rowcount,
                        "truncated": data_truncated,
                    }
                else:
                    # Non-SELECT query
                    conn.commit()
                    return {
                        "success": True,
                        "row_count": cur.rowcount,
                        "columns": [],
                        "data": [],
                    }

        except Exception as e:
            self.logger.error(f"Query execution failed: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_schema_info(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Get schema information for all tables in the database.

        Returns:
            Dictionary mapping table names to lists of column information dictionaries
        """
        self.logger.info("Retrieving schema information")

        try:
            schema_query = """
            SELECT
                t.table_name,
                c.column_name,
                c.data_type,
                c.column_default,
                c.is_nullable,
                pgd.description
            FROM
                information_schema.tables t
                JOIN information_schema.columns c ON t.table_name = c.table_name
                LEFT JOIN pg_catalog.pg_description pgd ON
                    pgd.objoid = (
                        SELECT oid FROM pg_catalog.pg_class 
                        WHERE relname = t.table_name
                    )
                    AND pgd.objsubid = c.ordinal_position
            WHERE
                t.table_schema = 'public'
                AND t.table_type = 'BASE TABLE'
            ORDER BY
                t.table_name,
                c.ordinal_position;
            """

            result = self.execute_query(schema_query)

            if not result["success"]:
                self.logger.error(
                    f"Failed to retrieve schema: {result['error']}"
                )
                return {}

            # Process the result into a more usable format
            schema_info = {}
            for row in result["data"]:
                table_name = row[0]
                column_info = {
                    "name": row[1],
                    "type": row[2],
                    "default": row[3],
                    "nullable": row[4] == "YES",
                    "description": row[5] or "",
                }

                if table_name not in schema_info:
                    schema_info[table_name] = []

                schema_info[table_name].append(column_info)

            return schema_info

        except Exception as e:
            self.logger.error(f"Error retrieving schema information: {str(e)}")
            return {}

    def get_table_relationships(self) -> List[Dict[str, str]]:
        """
        Get foreign key relationships between tables.

        Returns:
            List of dictionaries containing relationship information
        """
        self.logger.info("Retrieving table relationships")

        try:
            relationship_query = """
            SELECT
                tc.table_name AS table_name,
                kcu.column_name AS column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM
                information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY';
            """

            result = self.execute_query(relationship_query)

            if not result["success"]:
                self.logger.error(
                    f"Failed to retrieve relationships: {result['error']}"
                )
                return []

            relationships = []
            for row in result["data"]:
                relationship = {
                    "table": row[0],
                    "column": row[1],
                    "foreign_table": row[2],
                    "foreign_column": row[3],
                }
                relationships.append(relationship)

            return relationships

        except Exception as e:
            self.logger.error(f"Error retrieving table relationships: {str(e)}")
            return []

    def get_tables(self) -> List[str]:
        """
        Get a list of all tables in the database.

        Returns:
            List of table names
        """
        self.logger.info("Retrieving table list")

        try:
            tables_query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
            """

            result = self.execute_query(tables_query)

            if not result["success"]:
                self.logger.error(
                    f"Failed to retrieve tables: {result['error']}"
                )
                return []

            return [row[0] for row in result["data"]]

        except Exception as e:
            self.logger.error(f"Error retrieving table list: {str(e)}")
            return []

    def __del__(self):
        """Destructor to ensure connection is closed."""
        self.close()
