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
    has_correct_formula = check_gross_sales_formula(parsed)

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
        "product_join": check_product_join(parsed),
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

def check_gross_sales_formula(parsed) -> bool:
    order_item_aliases = {
        table.alias_or_name.lower()
        for table in parsed.find_all(exp.Table)
        if table.name.lower() == "order_items"
    }

    for sum_expression in parsed.find_all(exp.Sum):
        multiplication = sum_expression.this

        if not isinstance(multiplication, exp.Mul):
            continue

        columns = list(multiplication.find_all(exp.Column))

        if len(columns) != 2:
            continue

        column_sources = {
            (column.name.lower(), column.table.lower())
            for column in columns
        }

        expected_columns = {
            ("unit_price", alias)
            for alias in order_item_aliases
        } | {
            ("quantity", alias)
            for alias in order_item_aliases
        }

        if (
            len(order_item_aliases) == 1
            and column_sources == {
                ("unit_price", next(iter(order_item_aliases))),
                ("quantity", next(iter(order_item_aliases))),
            }
        ):
            return True

    return False
        
def check_product_join(parsed) -> bool:
    table_aliases = {
        table.name.lower(): table.alias_or_name.lower()
        for table in parsed.find_all(exp.Table)
    }

    order_items_alias = table_aliases.get("order_items")
    products_alias = table_aliases.get("products")

    if not order_items_alias or not products_alias:
        return False

    for join in parsed.find_all(exp.Join):
        on_condition = join.args.get("on")

        if on_condition is None:
            continue

        for equality in on_condition.find_all(exp.EQ):
            left = equality.this
            right = equality.expression

            if not (
                isinstance(left, exp.Column)
                and isinstance(right, exp.Column)
            ):
                continue

            columns = {
                (left.table.lower(), left.name.lower()),
                (right.table.lower(), right.name.lower()),
            }

            if columns == {
                (order_items_alias, "product_id"),
                (products_alias, "product_id"),
            }:
                return True

    return False

