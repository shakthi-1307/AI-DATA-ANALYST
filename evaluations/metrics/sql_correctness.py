import sqlglot 
from sqlglot import exp 

def extract_tables(sql:str) -> set[str]:
    """Extract table names referenced in a SQL query."""
    
    try:
        parsed = sqlglot.parse_one(sql,read="postgres")
    except Exception:
        return set()
    
    return {
        table.name.lower()
        for table in parsed.find_all(exp.Table)
    }
        
def check_expected_tables(
    sql_queries:list[str],
    expected_tables:list[str]
) -> dict:
    actual_tables = set()
    
    for sql in sql_queries:
        actual_tables.update(extract_tables(sql))
        
    expected = {
        table.lower()
        for table in expected_tables
    }
    
    missing_tables = expected - actual_tables
    
    return {
        "passed": len(missing_tables) == 0,
        "expected_tables": sorted(expected),
        "actual_tables": sorted(actual_tables),
        "missing_tables": sorted(missing_tables)
    }
    

def check_gross_sales_expression(sql: str) -> dict:
    try:
        parsed = sqlglot.parse_one(sql, read="postgres")
    except Exception as error:
        return {
            "passed": False,
            "reason": f"SQL parsing failed: {error}"
        }

    # Find SUM expressions
    sum_expressions = list(
        parsed.find_all(exp.Sum)
    )

    # Check for unit_price * quantity
    has_correct_formula = False

    for sum_expression in sum_expressions:
        multiplication = sum_expression.this

        if not isinstance(multiplication, exp.Mul):
            continue

        columns = {
            column.name.lower()
            for column in multiplication.find_all(exp.Column)
        }

        if columns == {"unit_price", "quantity"}:
            has_correct_formula = True
            break

    # Check GROUP BY
    has_group_by = check_group_by_category(parsed)

    # Check ORDER BY
    order = parsed.args.get("order")
    has_order_by = check_order_by_gross_sales(parsed)
    
    # Check LIMIT 1
    limit = parsed.args.get("limit")
    has_limit_one = (
        limit is not None
        and limit.expression is not None
        and limit.expression.is_number
        and limit.expression.this == "1"
    )

    checks = {
        "correct_gross_sales_formula": has_correct_formula,
        "group_by": has_group_by,
        "order_by": has_order_by,
        "limit_one": has_limit_one,
        "source_tables": check_gross_sales_source_tables(parsed),
    }

    return {
        "passed": all(checks.values()),
        "checks": checks
    }

def check_group_by_category(parsed) -> bool:
    group = parsed.args.get("group")

    if group is None:
        return False

    product_aliases = {
        table.alias_or_name.lower()
        for table in parsed.find_all(exp.Table)
        if table.name.lower() == "products"
    }

    for column in group.find_all(exp.Column):
        if (
            column.name.lower() == "category"
            and column.table.lower() in product_aliases
        ):
            return True

    return False

def check_order_by_gross_sales(parsed) -> bool:
    order = parsed.args.get("order")
    
    if order is None or not order.expressions:
        return False 
    
    for ordering in order.expressions:
        expression = ordering.this 
        
        if (
            isinstance(expression, exp.Column)
            and expression.name.lower() == "gross_sales"
            and ordering.args.get("desc") is True 
        ):
            return True 
    
    return False

def check_gross_sales_source_tables(parsed) -> bool:
    tables = {
        table.name.lower()
        for table in parsed.find_all(exp.Table)
    }
    
    return {"order_items","products"}.issubset(tables)