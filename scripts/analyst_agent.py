import os 
import sys 
import asyncio 
from pathlib import Path 
from typing import TypedDict, Annotated
from dotenv import load_dotenv
from langchain_groq import ChatGroq 
from langchain_core.messages import SystemMessage,HumanMessage
from langchain_core.messages import AnyMessage 
from langgraph.graph import StateGraph, START, END 
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition 
from langchain_mcp_adapters.client import MultiServerMCPClient 

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = PROJECT_ROOT / "scripts" / "db_mcp_server.py"

class AnlaystState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]