import pandas as pd
from typing import Dict, List, Any
from .data_loader import get_returns_data, get_sales_data, get_products_data

def get_total_returns() -> int:
    """Get the total number of items returned historically."""
    df = get_returns_data()
    return int(df['quantity'].sum())

def get_returns_by_product() -> List[Dict[str, Any]]:
    """Get total returns broken down by product."""
    df = get_returns_data()
    grouped = df.groupby('product_id')['quantity'].sum().reset_index()
    return grouped.to_dict(orient='records')

def get_returns_by_category() -> List[Dict[str, Any]]:
    """Get total returns broken down by product category."""
    returns = get_returns_data()
    products = get_products_data()
    df = returns.merge(products, on='product_id', how='left')
    grouped = df.groupby('category')['quantity'].sum().reset_index()
    return grouped.to_dict(orient='records')

def get_returns_by_reason() -> List[Dict[str, Any]]:
    """Get the distribution of return reasons."""
    df = get_returns_data()
    grouped = df.groupby('return_reason')['quantity'].sum().reset_index()
    return grouped.to_dict(orient='records')

def get_return_rate(product_id: str = None) -> float:
    """Calculate return rate (returned quantity / sold quantity). Optionally for a specific product."""
    sales = get_sales_data()
    returns = get_returns_data()
    
    if product_id:
        sales = sales[sales['product_id'] == product_id]
        returns = returns[returns['product_id'] == product_id]
        
    total_sold = sales['quantity'].sum()
    total_returned = returns['quantity'].sum()
    
    if total_sold == 0:
        return 0.0
        
    return round((total_returned / total_sold) * 100, 2)

def identify_products_with_high_return_rates(threshold: float = 10.0) -> List[Dict[str, Any]]:
    """Identify products where the return rate exceeds the given percentage threshold."""
    sales = get_sales_data()
    returns = get_returns_data()
    
    sold_qty = sales.groupby('product_id')['quantity'].sum().reset_index(name='sold')
    returned_qty = returns.groupby('product_id')['quantity'].sum().reset_index(name='returned')
    
    merged = pd.merge(sold_qty, returned_qty, on='product_id', how='left').fillna(0)
    merged['return_rate'] = (merged['returned'] / merged['sold'] * 100).round(2)
    
    high_returns = merged[merged['return_rate'] > threshold].sort_values(by='return_rate', ascending=False)
    return high_returns.to_dict(orient='records')

def compare_return_rates_between_periods(start_date: str, end_date: str, comparison_start_date: str, comparison_end_date: str, product_id: str = None) -> Dict[str, Any]:
    """Compare the return rate of a specific product (or overall) between two date periods."""
    sales = get_sales_data()
    returns = get_returns_data()
    
    if product_id:
        sales = sales[sales['product_id'] == product_id]
        returns = returns[returns['product_id'] == product_id]
        
    def _rate(s, r, start, end):
        s_mask = (s['order_date'] >= pd.to_datetime(start)) & (s['order_date'] <= pd.to_datetime(end))
        r_mask = (r['return_date'] >= pd.to_datetime(start)) & (r['return_date'] <= pd.to_datetime(end))
        sold = s[s_mask]['quantity'].sum()
        ret = r[r_mask]['quantity'].sum()
        return (ret / sold * 100) if sold > 0 else 0.0
        
    current_rate = _rate(sales, returns, start_date, end_date)
    prev_rate = _rate(sales, returns, comparison_start_date, comparison_end_date)
    
    return {
        "product_id": product_id if product_id else "ALL",
        "current_period": f"{start_date} to {end_date}",
        "comparison_period": f"{comparison_start_date} to {comparison_end_date}",
        "current_return_rate": round(current_rate, 2),
        "previous_return_rate": round(prev_rate, 2),
        "absolute_change": round(current_rate - prev_rate, 2)
    }
