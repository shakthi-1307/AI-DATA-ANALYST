
import os
import json
import re

import psycopg
import sqlglot

from psycopg.rows import dict_row
from dotenv import load_dotenv
from sqlglot import exp
from mcp.server import MCPServer

load_dotenv()

# -----------------------------
# MCP SERVER
# -----------------------------

mcp = MCPServer("Ecommerce Analytics Database")


# -----------------------------
# DATABASE CONNECTION
# -----------------------------

def get_connection():

    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user="analyst_readonly",
        password=os.getenv("ANALYST_DB_PASSWORD"),
        options="-c default_transaction_read_only=on -c statement_timeout=10000",
        row_factory=dict_row
    )


# -----------------------------
# TOOL 1: LIST TABLES
# -----------------------------

@mcp.tool()
def list_tables() -> str:
    """List all available tables in the public PostgreSQL schema."""

    with get_connection() as conn:

        rows = conn.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """
        ).fetchall()

    return json.dumps(rows)


# -----------------------------
# TOOL 2: DESCRIBE TABLE
# -----------------------------

@mcp.tool()
def describe_table(table_name: str) -> str:
    """Get column names, data types and constraints for a public database table."""

    if not re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_]*", table_name):
        return "Invalid table name."

    with get_connection() as conn:

        exists = conn.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = %s
                  AND table_type = 'BASE TABLE'
            )
            """,
            (table_name,)
        ).fetchone()["exists"]

        if not exists:
            return f"Table '{table_name}' does not exist."

        columns = conn.execute(
            """
            SELECT
                column_name,
                data_type,
                is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
            ORDER BY ordinal_position
            """,
            (table_name,)
        ).fetchall()

        
        constraints = conn.execute(
            """
            SELECT
                con.conname AS constraint_name,

                CASE con.contype
                    WHEN 'p' THEN 'PRIMARY KEY'
                    WHEN 'f' THEN 'FOREIGN KEY'
                    WHEN 'u' THEN 'UNIQUE'
                    WHEN 'c' THEN 'CHECK'
                    ELSE con.contype::text
                END AS constraint_type,

                pg_get_constraintdef(con.oid) AS definition

            FROM pg_constraint con

            JOIN pg_class rel
                ON rel.oid = con.conrelid

            JOIN pg_namespace ns
                ON ns.oid = rel.relnamespace

            WHERE ns.nspname = 'public'
              AND rel.relname = %s

            ORDER BY con.contype, con.conname
            """,
            (table_name,)
        ).fetchall()


    return json.dumps({
        "table": table_name,
        "columns": columns,
        "constraints": constraints
    })


# -----------------------------
# SQL VALIDATION
# -----------------------------

def validate_sql(sql: str):

    try:

        statements = sqlglot.parse(sql, read="postgres")

        if len(statements) != 1 or statements[0] is None:
            return False, "Only one SQL statement is allowed."

        expression = statements[0]

        # Only read queries are permitted.
        if not isinstance(
            expression,
            (exp.Select, exp.Union, exp.Intersect, exp.Except)
        ):
            return False, "Only SELECT queries are allowed."

        # Reject dangerous operations anywhere in the query tree.
        forbidden = (
            exp.Insert,
            exp.Update,
            exp.Delete,
            exp.Create,
            exp.Drop,
            exp.Alter,
            exp.Command,
            exp.Merge
        )

        if any(expression.find_all(*forbidden)):
            return False, "Unsafe SQL operation detected."

        return True, "SQL validation successful."

    except Exception as error:

        return False, f"Invalid SQL: {str(error)}"


# -----------------------------
# TOOL 3: EXECUTE READ-ONLY SQL
# -----------------------------

@mcp.tool()
def run_readonly_query(sql: str) -> str:
    """Validate and execute a read-only PostgreSQL SELECT query.
    Returns at most 500 rows."""

    is_valid, message = validate_sql(sql)

    if not is_valid:
        return message

    # Enforce a maximum result size.
    safe_sql = f"SELECT * FROM ({sql.rstrip().rstrip(';')}) AS limited_result LIMIT 500"

    try:

        with get_connection() as conn:

            rows = conn.execute(safe_sql).fetchall()

        return json.dumps({
            "success": True,
            "row_count": len(rows),
            "truncated_or_limited": len(rows) == 500,
            "results": rows
        }, default=str)

    except Exception as error:

        return json.dumps({
            "success": False,
            "error": str(error)
        })


# -----------------------------
# START MCP SERVER
# -----------------------------

if __name__ == "__main__":

    mcp.run()
