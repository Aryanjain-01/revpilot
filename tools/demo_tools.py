import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from tools.registry import AVAILABLE_TOOLS

def print_result(title, result):
    print(f"\n--- {title} ---")
    print(json.dumps(result, indent=2))

def main():
    print("Running RevPilot Data Tools Demo...")
    
    # 1. Calculate total revenue
    rev = AVAILABLE_TOOLS['calculate_total_revenue']()
    print_result("Total Historical Revenue", rev)
    
    # 2. Compare two periods
    comp = AVAILABLE_TOOLS['compare_period_revenue'](
        start_date='2023-10-01', end_date='2023-10-31',
        comparison_start_date='2023-09-01', comparison_end_date='2023-09-30'
    )
    print_result("Revenue Comparison (Oct vs Sept)", comp)
    
    # 3. Find products with high stockout frequency
    stockouts = AVAILABLE_TOOLS['identify_products_with_high_stockout_frequency'](threshold_days=10)
    print_result("Products with >10 Stockout Days", stockouts)
    
    # 4. Find declining customers (Oct vs Sept)
    churn = AVAILABLE_TOOLS['identify_declining_customers'](
        start_date='2023-10-01', end_date='2023-10-31',
        comparison_start_date='2023-09-01', comparison_end_date='2023-09-30',
        threshold=-500.0
    )
    # Just show top 3 to keep output clean
    print_result("Top 3 Declining Customers (Oct vs Sept)", churn[:3])
    
    # 5. Find products with high return rates
    returns = AVAILABLE_TOOLS['identify_products_with_high_return_rates'](threshold=20.0)
    print_result("Products with >20% Return Rate", returns)
    
if __name__ == "__main__":
    main()
