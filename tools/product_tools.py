import pandas as pd
from typing import Dict, List, Any
from .data_loader import get_sales_data, get_products_data

def get_product_details(product_id: str) -> Dict[str, Any]:
    """Get static details (category, cost, price) for a specific product."""
    products = get_products_data()
    product = products[products['product_id'] == product_id]
    if product.empty:
        raise ValueError(f"Product not found: {product_id}")
    return product.iloc[0].to_dict()

def get_product_performance(product_id: str) -> Dict[str, Any]:
    """Get total lifetime sales, revenue, and profit for a specific product."""
    sales = get_sales_data()
    product_sales = sales[sales['product_id'] == product_id]
    
    if product_sales.empty:
        return {
            "product_id": product_id,
            "total_quantity": 0,
            "total_revenue": 0.0,
            "total_profit": 0.0,
            "total_orders": 0
        }
        
    return {
        "product_id": product_id,
        "total_quantity": int(product_sales['quantity'].sum()),
        "total_revenue": round(float(product_sales['revenue'].sum()), 2),
        "total_profit": round(float(product_sales['profit'].sum()), 2),
        "total_orders": int(product_sales['order_id'].nunique())
    }

def get_product_profitability() -> List[Dict[str, Any]]:
    """List all products with their total revenue, profit, and calculated margin."""
    sales = get_sales_data()
    grouped = sales.groupby('product_id').agg(total_revenue=('revenue', 'sum'), total_profit=('profit', 'sum')).reset_index()
    grouped['margin_percentage'] = (grouped['total_profit'] / grouped['total_revenue'] * 100).fillna(0).round(2)
    grouped['total_revenue'] = grouped['total_revenue'].round(2)
    grouped['total_profit'] = grouped['total_profit'].round(2)
    return grouped.to_dict(orient='records')

def get_top_products(by: str = 'revenue', top_n: int = 10) -> List[Dict[str, Any]]:
    """Get the top N products by either 'revenue', 'profit', or 'quantity'."""
    if by not in ['revenue', 'profit', 'quantity']:
        raise ValueError("Parameter 'by' must be 'revenue', 'profit', or 'quantity'")
        
    sales = get_sales_data()
    grouped = sales.groupby('product_id')[by].sum().reset_index()
    grouped = grouped.sort_values(by=by, ascending=False).head(top_n)
    if by != 'quantity':
        grouped[by] = grouped[by].round(2)
    return grouped.to_dict(orient='records')

def compare_product_performance_between_periods(start_date: str, end_date: str, comparison_start_date: str, comparison_end_date: str) -> List[Dict[str, Any]]:
    """Compare product performance (revenue, volume) between two periods."""
    sales = get_sales_data()
    
    mask1 = (sales['order_date'] >= pd.to_datetime(start_date)) & (sales['order_date'] <= pd.to_datetime(end_date))
    mask2 = (sales['order_date'] >= pd.to_datetime(comparison_start_date)) & (sales['order_date'] <= pd.to_datetime(comparison_end_date))
    
    period1 = sales[mask1].groupby('product_id').agg(current_revenue=('revenue', 'sum'), current_qty=('quantity', 'sum')).reset_index()
    period2 = sales[mask2].groupby('product_id').agg(previous_revenue=('revenue', 'sum'), previous_qty=('quantity', 'sum')).reset_index()
    
    comparison = pd.merge(period2, period1, on='product_id', how='outer').fillna(0)
    comparison['revenue_change'] = (comparison['current_revenue'] - comparison['previous_revenue']).round(2)
    comparison['current_revenue'] = comparison['current_revenue'].round(2)
    comparison['previous_revenue'] = comparison['previous_revenue'].round(2)
    
    return comparison.to_dict(orient='records')

def get_declining_products(start_date: str, end_date: str, comparison_start_date: str, comparison_end_date: str, threshold: float = -100.0) -> List[Dict[str, Any]]:
    """Identify products whose revenue dropped by more than `threshold` between two periods."""
    comparison = compare_product_performance_between_periods(start_date, end_date, comparison_start_date, comparison_end_date)
    declining = [p for p in comparison if p['revenue_change'] <= threshold]
    declining.sort(key=lambda x: x['revenue_change'])
    return declining
