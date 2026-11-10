
import asyncio
import sys

from pathlib import Path
from langchain_mcp_adapters.client import MultiServerMCPClient


# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = PROJECT_ROOT / "scripts" / "db_mcp_server.py"


async def main():

    # Connect to our PostgreSQL MCP server
    client = MultiServerMCPClient(
        {
            "ecommerce_db": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [str(SERVER_PATH)],
                "cwd": str(PROJECT_ROOT),
            }
        }
    )

    # Discover MCP tools
    tools = await client.get_tools()

    print("\nCONNECTED TO MCP SERVER")
    print("\nDISCOVERED TOOLS")

    for tool in tools:
        print(f"\nTool: {tool.name}")
        print(f"Description: {tool.description}")
        print(f"Arguments: {tool.args_schema}")

    # Create a tool lookup
    tool_map = {tool.name: tool for tool in tools}

    # Test 1: List tables
    print("\n--- TEST 1: LIST TABLES ---")

    result = await tool_map["list_tables"].ainvoke({})

    print(result)

    # Test 2: Describe orders
    print("\n--- TEST 2: DESCRIBE ORDERS ---")

    result = await tool_map["describe_table"].ainvoke(
        {"table_name": "orders"}
    )

    print(result)

    # Test 3: Execute analytical query
    print("\n--- TEST 3: EXECUTE QUERY ---")

    result = await tool_map["run_readonly_query"].ainvoke(
        {
            "sql": """
                SELECT category, COUNT(*) AS total
                FROM products
                GROUP BY category
                ORDER BY total DESC
            """
        }
    )

    print(result)

    print("\nALL TESTS COMPLETED")


if __name__ == "__main__":
    asyncio.run(main())
