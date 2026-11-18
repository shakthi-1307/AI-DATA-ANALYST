
from evaluations.metrics.sql_correctness import (
    check_gross_sales_expression
)


def test_correct_gross_sales_query():
    sql = """
        SELECT p.category,
               SUM(oi.unit_price * oi.quantity) AS gross_sales
        FROM order_items oi
        JOIN products p
          ON oi.product_id = p.product_id
        GROUP BY p.category
        ORDER BY gross_sales DESC
        LIMIT 1
    """

    result = check_gross_sales_expression(sql)

    assert result["passed"] is True


def test_incorrect_gross_sales_formula():
    sql = """
        SELECT SUM(unit_price)
        FROM order_items
        GROUP BY product_id
        ORDER BY SUM(unit_price) DESC
        LIMIT 1
    """

    result = check_gross_sales_expression(sql)

    assert result["passed"] is False
    assert result["checks"]["correct_gross_sales_formula"] is False
