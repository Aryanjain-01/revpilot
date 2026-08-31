from langchain_core.tools import tool
from tools.registry import AVAILABLE_TOOLS

_COMPARISON_CACHE = {}


def _comparison_key(tool_name: str, start_date: str, end_date: str, comparison_start_date: str, comparison_end_date: str) -> tuple:
    return (tool_name, start_date, end_date, comparison_start_date, comparison_end_date)


def _invert_period_comparison(result: dict, metric_name: str) -> dict:
    current_value_key = f"current_{metric_name}"
    previous_value_key = f"previous_{metric_name}"
    current_value = result[current_value_key]
    previous_value = result[previous_value_key]
    absolute_change = round(previous_value - current_value, 2)
    percentage_change = round((absolute_change / current_value * 100) if current_value else 0, 2)

    return {
        "current_period": result["comparison_period"],
        "comparison_period": result["current_period"],
        current_value_key: previous_value,
        previous_value_key: current_value,
        "absolute_change": absolute_change,
        "percentage_change": percentage_change,
    }


def _run_cached_period_comparison(
    tool_name: str,
    metric_name: str,
    start_date: str,
    end_date: str,
    comparison_start_date: str,
    comparison_end_date: str,
) -> dict:
    key = _comparison_key(tool_name, start_date, end_date, comparison_start_date, comparison_end_date)
    if key in _COMPARISON_CACHE:
        return _COMPARISON_CACHE[key]

    reverse_key = _comparison_key(tool_name, comparison_start_date, comparison_end_date, start_date, end_date)
    if reverse_key in _COMPARISON_CACHE:
        result = _invert_period_comparison(_COMPARISON_CACHE[reverse_key], metric_name)
        _COMPARISON_CACHE[key] = result
        return result

    result = AVAILABLE_TOOLS[tool_name](start_date, end_date, comparison_start_date, comparison_end_date)
    _COMPARISON_CACHE[key] = result
    return result


# --- SALES TOOLS ---
@tool
def compare_period_revenue(start_date: str, end_date: str, comparison_start_date: str, comparison_end_date: str) -> dict:
    """Compare revenue between two date ranges (YYYY-MM-DD). A single result can be interpreted in either direction; do not call again with the same periods swapped."""
    return _run_cached_period_comparison(
        'compare_period_revenue',
        'revenue',
        start_date,
        end_date,
        comparison_start_date,
        comparison_end_date,
    )

@tool
def compare_period_profit(start_date: str, end_date: str, comparison_start_date: str, comparison_end_date: str) -> dict:
    """Compare profit between two date ranges (YYYY-MM-DD). A single result can be interpreted in either direction; do not call again with the same periods swapped."""
    return _run_cached_period_comparison(
        'compare_period_profit',
        'profit',
        start_date,
        end_date,
        comparison_start_date,
        comparison_end_date,
    )

@tool
def get_product_performance(product_id: str) -> dict:
    """Get total lifetime sales, revenue, and profit for a specific product."""
    return AVAILABLE_TOOLS['get_product_performance'](product_id)

@tool
def compare_product_performance_between_periods(start_date: str, end_date: str, comparison_start_date: str, comparison_end_date: str) -> list:
    """Compare product performance (revenue, volume) between two periods."""
    return AVAILABLE_TOOLS['compare_product_performance_between_periods'](start_date, end_date, comparison_start_date, comparison_end_date)

# --- INVENTORY TOOLS ---
@tool
def get_stockout_days(product_id: str) -> dict:
    """Get the number of days a specific product was out of stock."""
    return AVAILABLE_TOOLS['get_stockout_days'](product_id)

@tool
def identify_products_with_high_stockout_frequency(threshold_days: int = 5) -> list:
    """Find all products that have been out of stock for more than `threshold_days`."""
    return AVAILABLE_TOOLS['identify_products_with_high_stockout_frequency'](threshold_days)

# --- CUSTOMER TOOLS ---
@tool
def compare_customer_activity_between_periods(start_date: str, end_date: str, comparison_start_date: str, comparison_end_date: str) -> list:
    """Compare each customer's revenue and order count between two periods."""
    return AVAILABLE_TOOLS['compare_customer_activity_between_periods'](start_date, end_date, comparison_start_date, comparison_end_date)

@tool
def identify_declining_customers(start_date: str, end_date: str, comparison_start_date: str, comparison_end_date: str, threshold: float = -100.0) -> list:
    """Identify customers whose revenue dropped by more than a threshold between two periods."""
    return AVAILABLE_TOOLS['identify_declining_customers'](start_date, end_date, comparison_start_date, comparison_end_date, threshold)

# --- RETURNS TOOLS ---
@tool
def identify_products_with_high_return_rates(threshold: float = 10.0) -> list:
    """Identify products where the return rate exceeds the given percentage threshold."""
    return AVAILABLE_TOOLS['identify_products_with_high_return_rates'](threshold)
