"""
Tool Registry

This module exposes all available tools in a centralized location for future agents.
"""

from .sales_tools import (
    calculate_total_revenue,
    calculate_total_profit,
    calculate_revenue_by_month,
    calculate_profit_by_month,
    calculate_sales_by_product,
    calculate_sales_by_category,
    calculate_sales_by_region,
    calculate_sales_by_customer_segment,
    compare_period_revenue,
    compare_period_profit
)

from .inventory_tools import (
    get_stockout_summary,
    get_product_inventory_history,
    get_stockout_days,
    get_inventory_by_date_range,
    identify_products_with_high_stockout_frequency,
    get_restock_events
)

from .customer_tools import (
    get_customer_revenue,
    get_customer_order_count,
    get_revenue_by_customer_segment,
    get_revenue_by_region,
    identify_declining_customers,
    identify_high_value_customers,
    compare_customer_activity_between_periods
)

from .product_tools import (
    get_product_details,
    get_product_performance,
    get_top_products,
    get_declining_products,
    get_product_profitability,
    compare_product_performance_between_periods
)

from .returns_tools import (
    get_total_returns,
    get_returns_by_product,
    get_returns_by_category,
    get_returns_by_reason,
    get_return_rate,
    identify_products_with_high_return_rates,
    compare_return_rates_between_periods
)

# A simple dictionary registry
AVAILABLE_TOOLS = {
    # Sales
    "calculate_total_revenue": calculate_total_revenue,
    "calculate_total_profit": calculate_total_profit,
    "calculate_revenue_by_month": calculate_revenue_by_month,
    "calculate_profit_by_month": calculate_profit_by_month,
    "calculate_sales_by_product": calculate_sales_by_product,
    "calculate_sales_by_category": calculate_sales_by_category,
    "calculate_sales_by_region": calculate_sales_by_region,
    "calculate_sales_by_customer_segment": calculate_sales_by_customer_segment,
    "compare_period_revenue": compare_period_revenue,
    "compare_period_profit": compare_period_profit,
    
    # Inventory
    "get_stockout_summary": get_stockout_summary,
    "get_product_inventory_history": get_product_inventory_history,
    "get_stockout_days": get_stockout_days,
    "get_inventory_by_date_range": get_inventory_by_date_range,
    "identify_products_with_high_stockout_frequency": identify_products_with_high_stockout_frequency,
    "get_restock_events": get_restock_events,
    
    # Customers
    "get_customer_revenue": get_customer_revenue,
    "get_customer_order_count": get_customer_order_count,
    "get_revenue_by_customer_segment": get_revenue_by_customer_segment,
    "get_revenue_by_region": get_revenue_by_region,
    "identify_declining_customers": identify_declining_customers,
    "identify_high_value_customers": identify_high_value_customers,
    "compare_customer_activity_between_periods": compare_customer_activity_between_periods,
    
    # Products
    "get_product_details": get_product_details,
    "get_product_performance": get_product_performance,
    "get_top_products": get_top_products,
    "get_declining_products": get_declining_products,
    "get_product_profitability": get_product_profitability,
    "compare_product_performance_between_periods": compare_product_performance_between_periods,
    
    # Returns
    "get_total_returns": get_total_returns,
    "get_returns_by_product": get_returns_by_product,
    "get_returns_by_category": get_returns_by_category,
    "get_returns_by_reason": get_returns_by_reason,
    "get_return_rate": get_return_rate,
    "identify_products_with_high_return_rates": identify_products_with_high_return_rates,
    "compare_return_rates_between_periods": compare_return_rates_between_periods,
}
