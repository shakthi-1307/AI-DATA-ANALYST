
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
    
def test_wrong_group_by_column():
    sql = """
        SELECT product_id,
                SUM(unit_price * quantity) AS gross_sales
        FROM order_items
        GROUP BY product_id
        ORDER BY gross_sales DESC 
        LIMIT 1
    """
    
    result = check_gross_sales_expression(sql)
    
    assert result["passed"] is False 
    assert result["checks"]["group_by"] is False
    

def test_wrong_order_by_column():
    sql = """
        SELECT p.category,
               SUM(oi.unit_price * oi.quantity) AS gross_sales
        FROM order_items oi
        JOIN products p
          ON oi.product_id = p.product_id
        GROUP BY p.category
        ORDER BY p.category DESC
        LIMIT 1
    """

    result = check_gross_sales_expression(sql)

    assert result["passed"] is False
    assert result["checks"]["order_by"] is False


def test_ascending_order_is_rejected():
    sql = """
        SELECT p.category,
               SUM(oi.unit_price * oi.quantity) AS gross_sales
        FROM order_items oi
        JOIN products p
          ON oi.product_id = p.product_id
        GROUP BY p.category
        ORDER BY gross_sales ASC
        LIMIT 1
    """

    result = check_gross_sales_expression(sql)

    assert result["passed"] is False
    assert result["checks"]["order_by"] is False

def test_addition_is_rejected():
    sql = """
        SELECT SUM(unit_price + quantity) AS gross_sales
        FROM order_items
        GROUP BY product_id
        ORDER BY gross_sales DESC
        LIMIT 1
    """

    result = check_gross_sales_expression(sql)

    assert result["passed"] is False
    assert result["checks"]["correct_gross_sales_formula"] is False
    
def test_division_is_rejected():
    sql = """
        SELECT SUM(unit_price / quantity) AS gross_sales
        FROM order_items
        GROUP BY product_id
        ORDER BY gross_sales DESC
        LIMIT 1
    """

    result = check_gross_sales_expression(sql)

    assert result["passed"] is False
    assert result["checks"]["correct_gross_sales_formula"] is False
    
def test_missing_products_tables_is_rejected():
    sql = """
        SELECT SUM(unit_price * quantity) AS gross_sales
        FROM order_items
        GROUP BY category
        ORDER BY gross_sales DESC
        LIMIT 1 
    """
    
    result = check_gross_sales_expression(sql)
    
    assert result["passed"] is False 
    assert result["checks"]["source_tables"] is False 
    
def test_incorrect_product_join_is_rejected():
    sql = """
        SELECT 
            p.category,
            SUM(oi.unit_price * oi.quantity) AS gross_sales
        FROM order_items oi 
        JOIN products p 
            ON oi.order_id = p.product_id
        GROUP BY p.category
        ORDER BY gross_sales DESC
        LIMIT 1 
    """
    
    result = check_gross_sales_expression(sql)
    assert result["passed"] is False 
    assert result["checks"]["product_join"] is False
    
def test_wrong_category_source_is_rejected():
    sql = """
        SELECT 
            oi.product_id,
            SUM(oi.unit_price * oi.quantity) AS gross_sales 
        FROM order_items oi
        JOIN products p
            ON oi.product_id = p.product_id
        GROUP BY oi.product_id
        ORDER BY gross_sales DESC
        LIMIT 1 
    """
    
    result = check_gross_sales_expression(sql)
    assert result["passed"] is False 
    assert result["checks"]["group_by"] is False 
    
    
    
    
    
    
