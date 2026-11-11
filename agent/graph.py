from agent.llm import llm
from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, START, END 
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from agent.system_prompt import SYSTEM_PROMPT
from langchain_core.messages import SystemMessage, AnyMessage


class AnalystState(TypedDict):
    messages: Annotated[list[AnyMessage],add_messages]
    
def build_graph(tools):
    llm_with_tools = llm.bind_tools(tools)
    
    async def analyst_node(state: AnalystState):
        
        messages = [
            SystemMessage(content = SYSTEM_PROMPT),
            *state["messages"]
        ]
        
        response = await llm_with_tools.ainvoke(messages)
        return {"messages":[response]}
    
    graph = StateGraph(AnalystState)
    
    graph.add_node("analyst",analyst_node)
    
    graph.add_node("tools",ToolNode(tools))
    
    graph.add_edge(START,"analyst")
    
    graph.add_conditional_edges(
        "analyst",
        tools_condition,
        {
            "tools":"tools",
            END:END
        }
    )
    
    graph.add_edge("tools","analyst")
    
    return graph.compile()
    
    
    
    