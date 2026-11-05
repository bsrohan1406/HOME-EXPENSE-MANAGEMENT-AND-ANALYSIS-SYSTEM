"""
Database connection and query execution module for PennyWise Backend.

Features:
- MySQL connection pooling with mysql-connector-python
- Parameterized queries
- Dictionary cursors for JSON-friendly results
- Context-managed connection cleanup
- Safe database error messages

IMPORTANT:
Schema initialization is blocked by default if the SQL file contains
DROP or TRUNCATE statements.
"""

import logging
import os
import re
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple, Union

import mysql.connector
from mysql.connector import Error, pooling

from config import Config

logger = logging.getLogger(__name__)

# Global connection pool instance
_connection_pool: Optional[pooling.MySQLConnectionPool] = None


class DatabaseError(Exception):
    """Custom exception for database-related errors."""

    def __init__(
        self,
        message: str,
        original_error: Optional[Exception] = None
    ):
        super().__init__(message)
        self.original_error = original_error


def get_db_config(custom_config: Optional[dict] = None) -> dict:
    """Return the MySQL connection configuration."""

    if custom_config:
        return custom_config

    return {
        "host": Config.MYSQL_HOST,
        "port": Config.MYSQL_PORT,
        "user": Config.MYSQL_USER,
        "password": Config.MYSQL_PASSWORD,
        "database": Config.MYSQL_DATABASE,
        "charset": "utf8mb4",
        "collation": "utf8mb4_unicode_ci",
        "autocommit": False,
    }


def init_connection_pool(
    pool_size: Optional[int] = None
) -> Optional[pooling.MySQLConnectionPool]:
    """
    Initialize the MySQL connection pool.
    Uses Config.MYSQL_POOL_SIZE if no pool size is supplied.
    """

    global _connection_pool

    if pool_size is None:
        pool_size = Config.MYSQL_POOL_SIZE

    try:
        config = get_db_config()

        _connection_pool = pooling.MySQLConnectionPool(
            pool_name="pennywise_pool",
            pool_size=pool_size,
            pool_reset_session=True,
            **config
        )

        logger.info("MySQL connection pool initialized successfully.")
        return _connection_pool

    except Error:
        logger.exception("Could not initialize the MySQL connection pool.")
        _connection_pool = None
        return None


@contextmanager
def get_db_connection():
    """
    Provide a MySQL connection and ensure proper cleanup.
    """

    global _connection_pool
    conn = None

    try:
        if _connection_pool is not None:
            try:
                conn = _connection_pool.get_connection()

            except Error:
                logger.warning(
                    "Could not obtain a pooled connection. "
                    "Trying a direct connection."
                )
                conn = mysql.connector.connect(**get_db_config())

        else:
            conn = mysql.connector.connect(**get_db_config())

        yield conn

    except Error as err:
        logger.error("A MySQL connection operation failed.")

        raise DatabaseError(
            "Unable to connect to the database. Check the MySQL service "
            "and database configuration.",
            err
        ) from err

    finally:
        if conn is not None:
            try:
                conn.close()
            except Error:
                logger.warning("Could not cleanly close the MySQL connection.")


def test_connection() -> Tuple[bool, str]:
    """Check whether the configured MySQL database is reachable."""

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()

        return True, "Database connection is healthy"

    except Exception:
        logger.warning("Database connection test failed.")

        return False, (
            "Database connection failed. Check that MySQL is running "
            "and the credentials/database name in your .env file are correct."
        )


def execute_query(
    query: str,
    params: Optional[Union[tuple, list, dict]] = None,
    fetch_all: bool = False,
    fetch_one: bool = False,
    commit: bool = False
) -> Union[List[Dict[str, Any]], Optional[Dict[str, Any]], int]:
    """
    Execute a parameterized SQL query safely.

    Args:
        query: SQL statement using %s placeholders.
        params: Parameters matching the placeholders.
        fetch_all: Return all rows as a list of dictionaries.
        fetch_one: Return one row as a dictionary or None.
        commit: Commit the operation and return lastrowid/rowcount.
    """

    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(query, params or ())

            if commit:
                conn.commit()
                return cursor.lastrowid or cursor.rowcount

            if fetch_one:
                return cursor.fetchone()

            if fetch_all:
                return cursor.fetchall()

            return cursor.rowcount

        except Error as err:
            try:
                conn.rollback()
            except Exception:
                logger.warning("Database rollback failed.")

            logger.error("Database query execution failed.")

            raise DatabaseError(
                "Database operation failed.",
                err
            ) from err

        finally:
            try:
                cursor.close()
            except Error:
                logger.warning("Could not close the database cursor.")


def initialize_schema_if_needed(
    sql_file_path: Optional[str] = None,
    *,
    allow_destructive: bool = False
) -> bool:
    """
    Manually initialize the database from database/schema.sql.

    DROP and TRUNCATE statements are blocked unless
    allow_destructive=True is explicitly supplied.

    Back up your database before allowing destructive statements.
    Do not call this automatically during normal application startup.
    """

    if not sql_file_path:
        sql_file_path = os.path.join(
            os.path.dirname(__file__),
            "database",
            "schema.sql"
        )

    if not os.path.exists(sql_file_path):
        logger.warning("Schema file was not found.")
        return False

    try:
        with open(sql_file_path, "r", encoding="utf-8") as schema_file:
            sql_script = schema_file.read()

        # Remove SQL comments before checking destructive statements.
        sql_without_comments = re.sub(
            r"/\*.*?\*/|--[^\r\n]*|#[^\r\n]*",
            "",
            sql_script,
            flags=re.DOTALL
        )

        destructive_pattern = re.compile(
            r"\b(DROP|TRUNCATE)\s+(TABLE|DATABASE)\b",
            flags=re.IGNORECASE
        )

        if (
            destructive_pattern.search(sql_without_comments)
            and not allow_destructive
        ):
            logger.warning(
                "Schema initialization blocked because the SQL file "
                "contains DROP or TRUNCATE statements."
            )
            return False

        statements = [
            statement.strip()
            for statement in sql_without_comments.split(";")
            if statement.strip()
        ]

        with get_db_connection() as conn:
            cursor = conn.cursor()

            try:
                for statement in statements:
                    cursor.execute(statement)

                conn.commit()

            except Exception:
                conn.rollback()
                raise

            finally:
                cursor.close()

        logger.info("Database schema initialized successfully.")
        return True

    except Exception:
        logger.exception("Database schema initialization failed.")
        return False