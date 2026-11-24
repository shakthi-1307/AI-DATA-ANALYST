from evaluations.metrics.sql_correctness import (
    check_average_order_value_expression
)


def test_correct_average_order_value_query():
    sql = """
        SELECT
            SUM(amount) / COUNT(DISTINCT order_id) AS avg_order_value
        FROM payments
        WHERE payment_status = 'completed'
    """

    result = check_average_order_value_expression(sql)

    assert result["passed"] is True


def test_hardcoded_average_order_value_is_rejected():
    sql = """
        SELECT 264972113.82 / 8228 AS avg_order_value
    """

    result = check_average_order_value_expression(sql)

    assert result["passed"] is False
    
def test_wrong_source_table_is_rejected():
    sql = """
        SELECT
            SUM(amount) / COUNT(DISTINCT order_id) AS avg_order_value
        FROM orders
        WHERE payment_status = 'completed'
    """
    
    result = check_average_order_value_expression(sql)
    
    assert result["passed"] is False 
    assert result["checks"]["source_table"] is False

def test_or_condition_with_other_status_is_rejected():
    sql = """
        SELECT
            SUM(amount) / COUNT(DISTINCT order_id) AS avg_order_value
        FROM payments
        WHERE payment_status = 'completed'
           OR payment_status = 'pending'
    """

    result = check_average_order_value_expression(sql)

    assert result["passed"] is False
    
def test_count_without_distinct_is_rejected():
    sql = """
        SELECT 
            SUM(amount) / COUNT(order_id) AS avg_order_value
        FROM payments 
        WHERE payment_status = 'completed'
    """
    
    result = check_average_order_value_expression(sql)
    
    assert result["passed"] is False 
    assert result["checks"]["correct_formula"] is False
    

    