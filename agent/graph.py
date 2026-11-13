
from typing import TypedDict, Annotated

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import SystemMessage, AnyMessage, ToolMessage, AIMessage, HumanMessage
import json
from agent.llm import llm
from agent.system_prompt import SYSTEM_PROMPT

MAX_SQL_RETRIES = 2

class AnalystState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    sql_retry_count: int

def has_sql_error(messages):
    # Find the most recent AI message that requested tools
    last_ai_message = next(
        (
            message
            for message in reversed(messages)
            if getattr(message, "tool_calls", None)
        ),
        None
    )

    if not last_ai_message:
        return False

    # Only inspect results belonging to that tool-call batch
    tool_call_ids = {
        call["id"] for call in last_ai_message.tool_calls
    }

    for message in messages:
        if (
            isinstance(message, ToolMessage)
            and message.tool_call_id in tool_call_ids
            and message.name == "run_readonly_query"
        ):
            content = message.content

            # MCP responses may contain text blocks
            if isinstance(content, list):
                content = next(
                    (
                        block["text"]
                        for block in content
                        if block.get("type") == "text"
                    ),
                    "{}"
                )

            try:
                result = json.loads(content)
                if result.get("success") is False:
                    return True
            except (json.JSONDecodeError, TypeError):
                continue

    return False

def route_after_tools(state:AnalystState):
    if not has_sql_error(state["messages"]):
        return "analyst"
    
    retry_count = state.get("sql_retry_count",0)
    
    if retry_count < MAX_SQL_RETRIES:
        return "retry"
    
    return "failure"

def retry_node(state:AnalystState):
    retry_count = state.get("sql_retry_count",0) + 1 
    return {
        "sql_retry_count":retry_count,
        "messages":[
            HumanMessage(
                content = (
                    "Your previous SQL query failed. "
                    "Inspect the database error, correct the SQL query, and try again. "
                    "Do not repeat the same incorrect query."
                )
            )
        ]
    }

def failure_node(state:AnalystState):
    return {
        "messages":[
            AIMessage(
                content = (
                    "I couldn't complete the SQL analysis after "
                    f"{MAX_SQL_RETRIES} retry attempts. "
                    "Please review the query or try rephrasing your question. "
                )
            )
        ]
    }

def build_graph(tools):
    llm_with_tools = llm.bind_tools(tools)

    async def analyst_node(state: AnalystState):
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            *state["messages"]
        ]

        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    graph = StateGraph(AnalystState)

    graph.add_node("analyst", analyst_node)
    graph.add_node("tools", ToolNode(tools))
    graph.add_node("retry", retry_node)
    graph.add_node("failure", failure_node)

    graph.add_edge(START, "analyst")

    graph.add_conditional_edges(
        "analyst",
        tools_condition,
        {"tools": "tools", END: END}
    )

    graph.add_conditional_edges(
        "tools",
        route_after_tools,
        {
            "analyst": "analyst",
            "retry": "retry",
            "failure": "failure"
        }
    )

    graph.add_edge("retry", "analyst")
    graph.add_edge("failure", END)

    return graph.compile()