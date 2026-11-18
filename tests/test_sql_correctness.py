from evaluations.metrics.sql_correctness import (
    extract_tables,
    check_expected_tables
)

def test_extract_tables():
    sql = """
        SELECT p.category
        FROM products p
        JOIN order_items oi
        ON p.product_id = oi.product_id
    """
    
    assert extract_tables(sql) == {
        "products",
        "order_items"
    }
    
def test_expected_tables_pass():
    
    result = check_expected_tables(
        ["SELECT * FROM products"],
        ["products"]
    )
    
    assert result["passed"] is True 
    
def test_expected_tables_fail():
    
    result = check_expected_tables(
        ["SELECT * FROM products"],
        ["products","orders"]
    )
    
    assert result["passed"] is False 
    assert result["missing_tables"] == ["orders"]

def test_multiple_queries():
    queries = [
        "SELECT SUM(amount) FROM payments",
        "SELECT 264972113.82 / 8228 AS avg_order_value"
    ]

    result = check_expected_tables(
        queries,
        ["payments"]
    )

    assert result["passed"] is True
    assert result["actual_tables"] == ["payments"]