import os 
import sys 
import asyncio 
from dotenv import load_dotenv

from agent.graph import build_graph
from agent.mcp_connect import mcp_client

from langchain_core.messages import HumanMessage

load_dotenv()

async def main():
    
    client = mcp_client
    
    print("Connecting to PostgreSQL MCP server...")
    
    tools = await client.get_tools()
    
    print(f"Discovered {len(tools)} tools.")
    
    app = build_graph(tools)
    
    print("\nAI DATA ANALYST READY.")
    
    while True:
        question = input("\nAsk a business question (or type exit) : ")
        
        if question.strip().lower() in ("exit","quit"):
            break 
        
        if not question.strip():
            break
        
        print("\nAnalyzing...")
        
        try:
            result = await app.ainvoke(
                {
                    "messages":[
                        HumanMessage(content = question)
                    ],
                    "sql_retry_count":0
                },
                config = {"recursion_limit":12}
            )
            
            print("\n ------- AGENT EXECUTION TRACE ----")
            
            for message in result["messages"]:
                if getattr(message, "tool_calls", None):
                    print(f"\n[LLM] {message.__class__.__name__}")
                    
                    for tool_call in message.tool_calls:
                        print(f"Tool : {tool_call['name']}")
                        print(f"Arguments: {tool_call['args']}")
                elif message.type == "tool":
                    print(f"\n[TOOL RESULT] {message.name}")
                    print(message.content)
                    
            print("\n --------- FINAL BUSINESS ANALYSIS -------\n")
            
            final_message = result["messages"][-1]
            
            print("\nBUSINESS ANALYSIS")
            
            print(final_message.content)
            
        except Exception as error:
            print(f"\n Agent error : {error}")

if __name__ == "__main__":
    asyncio.run(main())
    
    

    
    