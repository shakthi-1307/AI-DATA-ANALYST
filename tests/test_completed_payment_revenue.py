
from evaluations.metrics.sql_correctness import (
    check_completed_payment_revenue,
)


def test_correct_completed_payment_revenue_query():
    sql = """
        SELECT SUM(amount) AS completed_payment_revenue
        FROM payments
        WHERE payment_status = 'completed';
    """

    result = check_completed_payment_revenue(sql)

    assert result["passed"] is True


def test_rejects_count_instead_of_sum():
    sql = """
        SELECT COUNT(amount) AS completed_payment_revenue
        FROM payments
        WHERE payment_status = 'completed';
    """

    result = check_completed_payment_revenue(sql)

    assert result["passed"] is False
    assert result["checks"]["sum_amount"] is False


def test_rejects_missing_payment_status_filter():
    sql = """
        SELECT SUM(amount) AS completed_payment_revenue
        FROM payments;
    """

    result = check_completed_payment_revenue(sql)

    assert result["passed"] is False
    assert result["checks"]["completed_payment_filter"] is False


def test_rejects_wrong_payment_status():
    sql = """
        SELECT SUM(amount) AS completed_payment_revenue
        FROM payments
        WHERE payment_status = 'pending';
    """

    result = check_completed_payment_revenue(sql)

    assert result["passed"] is False
    assert result["checks"]["completed_payment_filter"] is False


def test_rejects_wrong_source_table():
    sql = """
        SELECT SUM(amount) AS completed_payment_revenue
        FROM orders
        WHERE payment_status = 'completed';
    """

    result = check_completed_payment_revenue(sql)

    assert result["passed"] is False
    assert result["checks"]["source_table"] is False


def test_rejects_unsafe_or_condition():
    sql = """
        SELECT SUM(amount) AS completed_payment_revenue
        FROM payments
        WHERE payment_status = 'completed'
           OR payment_status = 'pending';
    """

    result = check_completed_payment_revenue(sql)

    assert result["passed"] is False
    assert result["checks"]["no_unsafe_or_condition"] is False

    
    
    
    