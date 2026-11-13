import pytest

from langchain_core.messages import AIMessage, ToolMessage, HumanMessage

from agent.graph import build_graph

import asyncio 
import json 
from langchain_core.tools import StructuredTool
import agent.graph as graph_module


class MockLLM:
    def __init__(self):
        self.attempts = 0

    def bind_tools(self, tools):
        return self

    async def ainvoke(self, messages):
        self.attempts += 1

        return AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "run_readonly_query",
                    "args": {
                        "sql": "SELECT fake_column FROM products"
                    },
                    "id": f"call_{self.attempts}",
                    "type": "tool_call"
                }
            ]
        )
        
async def fake_database_query(sql:str):
    return json.dumps({
        "success":False,
        "stage":"schema_validation",
        "error":"Column fake_column does not exist"
    })
    
def test_compiled_graph_stops_after_two_retries(monkeypatch):

    mock_llm = MockLLM()

    # Replace the real LLM with our mock
    monkeypatch.setattr(graph_module, "llm", mock_llm)

    # Create a mock SQL tool
    fake_tool = StructuredTool.from_function(
        coroutine=fake_database_query,
        name="run_readonly_query",
        description="Execute a read-only SQL query"
    )

    # Build the real LangGraph
    app = graph_module.build_graph([fake_tool])

    # Execute the graph
    result = asyncio.run(
        app.ainvoke(
            {
                "messages": [
                    HumanMessage(content="Calculate sales using fake_column")
                ],
                "sql_retry_count": 0
            },
            config={"recursion_limit": 15}
        )
    )

    # Verify the actual execution
    assert mock_llm.attempts == 3
    assert result["sql_retry_count"] == 2

    # Verify that the failure handler terminated the graph
    assert "couldn't complete the SQL analysis".lower() in (
        result["messages"][-1].content.lower()
    )
    
    