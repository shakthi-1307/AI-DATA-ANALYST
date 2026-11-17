import asyncio 
from langchain_core.messages import HumanMessage, ToolMessage 
from evaluations.dataset_loader import (
    load_golden_dataset,
    validate_dataset
)
from agent.graph import build_graph
from agent.mcp_connect import mcp_client
import json

async def evaluate_case(app, case):
    print(f"\nEvaluating: {case['id']}")
    print(f"Question: {case['question']}")
    
    result = await app.ainvoke(
        {
            "messages": [
                HumanMessage(content = case["question"])
            ],
            "sql_retry_count":0
        },
        config = {"recursion_limit":15}
    )
    
    sql_queries = []
    database_results = []
    
    for message in result["messages"]:
        if getattr(message,"tool_calls",None):
            for call in message.tool_calls:
                if call["name"] == "run_readonly_query":
                    sql_queries.append(call["args"]["sql"])
                    
        if isinstance(message,ToolMessage):
            if message.name == "run_readonly_query":
                parsed_result = parse_database_result(message.content)
                database_results.append(parsed_result)
                
    final_answer = result["messages"][-1].content
    
    return{
        "id": case["id"],
        "sql_queries":sql_queries,
        "database_results":database_results,
        "final_answer":final_answer,
        "retry_count": result.get("sql_retry_count",0)
    }
    
def parse_database_result(content):
    if isinstance(content,list):
        content = next(
            (
                block["text"]
                for block in content
                if block.get("type") == "text"
            ),
            "{}"
        )
        
    try:
        return json.loads(content)
    
    except (json.JSONDecodeError,TypeError):
        return {
            "success":False,
            "error":"Could not parse database response"
        }
        
async def main():
    dataset = load_golden_dataset()
    validate_dataset(dataset)
    
    print(f"Loaded {len(dataset)} evaluation cases.")
    
    tools = await mcp_client.get_tools()
    
    print(f"Discovered {len(tools)} MCP tools.")
    
    app = build_graph(tools)
    
    results = []
    
    for case in dataset:
        result = await evaluate_case(app,case)
        results.append(result)
        
        print("\nSQL queries generated:")
        for sql in result["sql_queries"]:
            print(sql)
            
        print("\nStructured database results:")

        for db_result in result["database_results"]:
            print(json.dumps(db_result, indent=2))
            
        print("\nFinal answer:")
        print(result["final_answer"])
        
        print(f"Retries: {result['retry_count']}")
        
    print(f"\nCompleted {len(results)} evaluation cases. ")
    
if __name__ == "__main__":
    asyncio.run(main())