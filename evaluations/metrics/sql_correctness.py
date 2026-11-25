import sqlglot 
from sqlglot import exp 

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
        

def check_average_order_value_expression(sql: str) -> dict:
    try:
        parsed = sqlglot.parse_one(sql, read="postgres")
    except Exception as error:
        return {
            "passed": False,
            "reason": str(error)
        }

    selects = list(parsed.find_all(exp.Select))

    # Check 1: SUM(amount) / COUNT(DISTINCT order_id)
    correct_division = False

    for division in parsed.find_all(exp.Div):
        numerator = division.this
        denominator = division.expression

        if not (
            isinstance(numerator, exp.Sum)
            and isinstance(denominator, exp.Count)
        ):
            continue

        numerator_column = numerator.this
        denominator_expression = denominator.this

        correct_numerator = (
            isinstance(numerator_column, exp.Column)
            and numerator_column.name.lower() == "amount"
        )

        correct_denominator = (
            isinstance(denominator_expression, exp.Distinct)
            and len(denominator_expression.expressions) == 1
            and isinstance(
                denominator_expression.expressions[0],
                exp.Column
            )
            and denominator_expression.expressions[0].name.lower() == "order_id"
        )

        if correct_numerator and correct_denominator:
            correct_division = True
            break

    # Check 2: AVG(order_total) over grouped payment totals
    correct_grouped_average = False

    for avg in parsed.find_all(exp.Avg):
        avg_column = avg.this

        if not (
            isinstance(avg_column, exp.Column)
            and avg_column.name.lower() == "order_total"
        ):
            continue

        for select in selects:
            has_sum_amount = any(
                isinstance(node, exp.Sum)
                and isinstance(node.this, exp.Column)
                and node.this.name.lower() == "amount"
                for node in select.find_all(exp.Sum)
            )

            group = select.args.get("group")

            has_order_id_grouping = (
                group is not None
                and any(
                    isinstance(column, exp.Column)
                    and column.name.lower() == "order_id"
                    for column in group.find_all(exp.Column)
                )
            )

            if has_sum_amount and has_order_id_grouping:
                correct_grouped_average = True
                break

    # Check 3: completed-payment filter in any query scope
    has_completed_filter = any(
        self_check_completed_filter(select)
        for select in selects
    )

    # Check 4: payments must be the source
    has_payments_table = any(
        table.name.lower() == "payments"
        for table in parsed.find_all(exp.Table)
    )

    checks = {
        "correct_formula": (
            correct_division or correct_grouped_average
        ),
        "completed_payment_filter": has_completed_filter,
        "source_table": has_payments_table,
    }

    return {
        "passed": all(checks.values()),
        "checks": checks,
    }


def self_check_completed_filter(select) -> bool:
    where = select.args.get("where")

    if not where:
        return False

    condition = where.this

    if condition.find(exp.Or):
        return False

    for equality in condition.find_all(exp.EQ):
        left = equality.this
        right = equality.expression

        if (
            isinstance(left, exp.Column)
            and left.name.lower() == "payment_status"
            and isinstance(right, exp.Literal)
            and right.this.lower() == "completed"
        ):
            return True

    return False


def check_average_order_value_queries(sql_queries: list[str]) -> dict:
    if len(sql_queries) != 1:
        return {
            "passed": False,
            "checks": {
                "single_query": False
            },
            "reason": "AOV must be calculated in one SQL query."
        }

    result = check_average_order_value_expression(sql_queries[0])

    if "checks" not in result:
        return result

    checks = {
        "single_query": True,
        **result["checks"]
    }

    return {
        "passed": all(checks.values()),
        "checks": checks
    }
