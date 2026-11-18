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
        multiplication = sum_expression.find(exp.Mul)

        if multiplication is None:
            continue

        columns = {
            column.name.lower()
            for column in multiplication.find_all(exp.Column)
        }

        if {"unit_price", "quantity"}.issubset(columns):
            has_correct_formula = True
            break

    # Check GROUP BY
    has_group_by = parsed.args.get("group") is not None

    # Check ORDER BY
    order = parsed.args.get("order")
    has_order_by = order is not None

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
        "limit_one": has_limit_one
    }

    return {
        "passed": all(checks.values()),
        "checks": checks
    }
