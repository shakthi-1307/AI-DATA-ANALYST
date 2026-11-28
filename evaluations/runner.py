import asyncio 
from langchain_core.messages import HumanMessage, ToolMessage 
from evaluations.dataset_loader import (
    load_golden_dataset,
    validate_dataset
)
from agent.graph import build_graph
from agent.mcp_connect import mcp_client
import json
from evaluations.metrics.result_accuracy import compare_results
from evaluations.metrics.sql_correctness import check_expected_tables
from evaluations.metrics.sql_correctness import (
    check_expected_tables,
    check_gross_sales_expression,
    check_average_order_value_expression,
    check_average_order_value_queries,
    check_completed_payment_revenue,
)
import time

async def evaluate_case(app, case):
    print(f"\nEvaluating: {case['id']}")
    print(f"Question: {case['question']}")
    
    start_time = time.perf_counter()

    result = await app.ainvoke(
        {
            "messages": [
                HumanMessage(content=case["question"])
            ],
            "sql_retry_count": 0
        },
        config={"recursion_limit": 15}
    )
    
    execution_time = round(time.perf_counter() - start_time,3)

    sql_queries = []
    database_results = []

    # Phase 1: Collect all SQL queries and database results
    for message in result["messages"]:

        if getattr(message, "tool_calls", None):
            for call in message.tool_calls:
                if call["name"] == "run_readonly_query":
                    sql_queries.append(call["args"]["sql"])

        if isinstance(message, ToolMessage):
            if message.name == "run_readonly_query":
                parsed_result = parse_database_result(message.content)
                database_results.append(parsed_result)
    
    sql_evaluation = check_expected_tables(
        sql_queries,
        case["expected_tables"]
    )
    
    semantic_evaluation = None

    if case["id"] == "eval_001" and sql_queries:
        semantic_evaluation = check_gross_sales_expression(sql_queries[0])

    elif case["id"] == "eval_002" and sql_queries:
        semantic_evaluation = check_completed_payment_revenue(sql_queries[0])

    elif case["id"] == "eval_004":
        semantic_evaluation = check_average_order_value_queries(sql_queries)

    # Phase 2: Evaluate after collecting all results
    accuracy = {}

    successful_results = [
        db_result
        for db_result in database_results
        if db_result.get("success")
    ]

    if successful_results:
        actual_result = {}

        # Merge fields from successful SQL queries.
        # Later results override duplicate keys.
        for db_result in successful_results:
            if db_result.get("results"):
                actual_result.update(db_result["results"][0])

        accuracy = compare_results(
            case["expected_result"],
            actual_result
        )

    final_answer = result["messages"][-1].content

    return {
        "id": case["id"],
        "sql_queries": sql_queries,
        "database_results": database_results,
        "final_answer": final_answer,
        "retry_count": result.get("sql_retry_count", 0),
        "accuracy": accuracy,
        "sql_evaluation": sql_evaluation,
        "semantic_evaluation": semantic_evaluation,
        "execution_time_seconds": execution_time,
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
from datetime import datetime,timezone
from pathlib import Path 


from datetime import datetime, timezone
from pathlib import Path


def save_evaluation_report(results):
    reports_dir = Path(__file__).parent / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc)

    report = {
        "evaluation_run": {
            "timestamp": timestamp.isoformat(),
            "total_cases": len(results),
            "passed": sum(
                1 for result in results
                if result["accuracy"]
                and all(
                    check["passed"]
                    for check in result["accuracy"].values()
                )
            ),
            "total_execution_time_seconds": round(
                sum(
                    result["execution_time_seconds"]
                    for result in results
                ),
                3
            )
        },
        "results": results
    }

    filename = (
        "evaluation_"
        + timestamp.strftime("%Y%m%d_%H%M%S")
        + ".json"
    )

    report_path = reports_dir / filename

    with report_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=4, ensure_ascii=False)

    print(f"\nEvaluation report saved: {report_path}")

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
        
        print("\nRESULT ACCURACY : ")
        for metric,comparison in result["accuracy"].items():
            status = "PASS" if comparison["passed"] else "FAIL"
            
            print(
                f"{metric}:{status} "
                f"(Expected: {comparison['expected']}, "
                f"Actual: {comparison['actual']})"
            )
        
        print("\nSQL CORRECTNESS:")
        
        evaluation = result["sql_evaluation"]
        
        status = "PASS" if evaluation["passed"] else "FAIL"

        print(f"Overall: {status}")
        print(f"Expected tables: {evaluation['expected_tables']}")
        print(f"Actual tables: {evaluation['actual_tables']}")
        print(f"Missing tables: {evaluation['missing_tables']}")
        
        if result["semantic_evaluation"] is not None:
            print("\nSQL SEMANTIC CORRECTNESS:")

            evaluation = result["semantic_evaluation"]

            print(
                "Overall:",
                "PASS" if evaluation["passed"] else "FAIL"
            )

            for check, passed in evaluation["checks"].items():
                print(
                    f"{check}:",
                    "PASS" if passed else "FAIL"
                )
        
        print(f"Retries: {result['retry_count']}")
        print(f"Execution time: {result['execution_time_seconds']} seconds")
        
    print(f"\nCompleted {len(results)} evaluation cases. ")
    save_evaluation_report(results)
    
if __name__ == "__main__":
    asyncio.run(main())