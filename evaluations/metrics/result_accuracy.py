
import math

FIELD_ALIASES = {
    "completed_payment_revenue": [
        "total_completed_payment_revenue",
        "total_completed_revenue"
    ],
    "average_order_value": [
        "avg_order_value"
    ]
}


def compare_results(
    expected: dict,
    actual: dict,
    relative_tolerance: float = 0.0001
):
    comparisons = {}

    for key, expected_value in expected.items():

        # Find the canonical field or an accepted alias
        possible_keys = [key] + FIELD_ALIASES.get(key, [])

        actual_key = next(
            (candidate for candidate in possible_keys
             if candidate in actual),
            None
        )

        if actual_key is None:
            comparisons[key] = {
                "passed": False,
                "expected": expected_value,
                "actual": None
            }
            continue

        actual_value = actual[actual_key]

        if isinstance(expected_value, (int, float)):
            passed = math.isclose(
                float(expected_value),
                float(actual_value),
                rel_tol=relative_tolerance,
                abs_tol=0.000001
            )
        else:
            passed = (
                str(expected_value).strip().lower()
                == str(actual_value).strip().lower()
            )

        comparisons[key] = {
            "passed": passed,
            "expected": expected_value,
            "actual": actual_value
        }

    return comparisons
