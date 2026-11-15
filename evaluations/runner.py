import asyncio 
from langchain_core.messages import HumanMessage, ToolMessage 
from evaluations.dataset_loader import (
    load_golden_dataset,
    validate_dataset
)
from agent.graph import build_graph
from agent.mcp_connect import mcp_client

async def evaluate_case(app, case):
    print(f"\nEvaluating: {case['id']}")
    print(f"Question: {case['question']}")