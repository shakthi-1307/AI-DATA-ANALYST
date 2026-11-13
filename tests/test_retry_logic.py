from langchain_core.messages import AIMessage, ToolMessage
from agent.graph import route_after_tools,retry_node

def make_state(success, retry_count=0):
    ai_message = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "run_readonly_query",
                "args": {"sql": "SELECT fake_column FROM products"},
                "id": "call_1",
                "type": "tool_call"
            }
        ]
    )

    tool_message = ToolMessage(
        content=(
            '{"success": true}' if success
            else '{"success": false, "stage": "schema_validation"}'
        ),
        tool_call_id="call_1",
        name="run_readonly_query"
    )

    return {
        "messages": [ai_message, tool_message],
        "sql_retry_count": retry_count
    }

def test_success_routes_to_analyst():
    assert route_after_tools(make_state(True)) == "analyst"


def test_failure_routes_to_retry():
    assert route_after_tools(make_state(False, 0)) == "retry"


def test_failure_at_retry_limit_routes_to_failure():
    assert route_after_tools(make_state(False, 2)) == "failure"
    
def test_retry_node_increments_counter():
    state = make_state(False,0)
    result = retry_node(state)
    assert result["sql_retry_count"] == 1 
    
def test_retry_node_increments_second_attempt():
    state = make_state(False,1)
    result = retry_node(state)
    assert result["sql_retry_count"] == 2