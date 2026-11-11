from scripts .db_mcp_server import validate_sql, validate_query_schema

test_cases = [
    
    (
        "valid SELECT",
        "SELECT * FROM products",
        True
    ),
    
    (
        "Valid JOIN",
        """
        SELECT p.category, SUM(oi.quantity)
        FROM products p
        JOIN order_items oi
        ON p.product_id = oi.product_id
        GROUP BY p.category
        """,
        True
    ),
    
    (
        "DELETE query",
        "DELETE FROM products",
        False
    ),
    
    (
        "UPDATE query",
        "UPDATE products SET price = 100",
        False
    ),
    
    (
        "Multiple statements",
        "SELECT * FROM products; DROP TABLE products;",
        False
    ),
    
    (
        "SELECT INTO",
        "SELECT * INTO new_table FROM products",
        False
    ),
    
    (
        "Invalid SQL",
        "SELECT FROM WHERE",
        False
    ),
]

schema_test_cases = [
    
    (
        "Exisitng Column",
        "SELECT product_name FROM products",
        True
    ),
    
    (
        "Nonexistent column",
        "SELECT nonexistent_column FROM products",
        False
    ),
    
    (
        "Nonexistent table",
        "SELECT * FROM nonexistent_table",
        False,
    )
]

for name,sql,expected in schema_test_cases:
    is_valid,message = validate_query_schema(sql)
    
    status = "PASS" if is_valid == expected else "FAIL"
    
    print(f"{status}: {name}")
    print(f"  Expected : {expected}")
    print(f"  Actual : {is_valid}")
    print(f"  Message : {message}")
    print()
    
for name,sql,expected in test_cases:
    is_valid,message = validate_sql(sql)
    
    status = "PASS" if is_valid == expected else "FAIL"
    
    print(f"{status}: {name}")
    print(f"  Expected : {expected}")
    print(f"  Actual : {is_valid}")
    print(f"  Message : {message}")
    print()