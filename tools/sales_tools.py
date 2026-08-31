import pandas as pd
from typing import Dict, List, Any
from .data_loader import get_sales_data, get_products_data, get_customers_data

def calculate_total_revenue(start_date: str = None, end_date: str = None) -> float:
    """Calculate total revenue, optionally within a date range (YYYY-MM-DD)."""
    df = get_sales_data()
    if start_date:
        df = df[df['order_date'] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df['order_date'] <= pd.to_datetime(end_date)]
    return round(float(df['revenue'].sum()), 2)

def calculate_total_profit(start_date: str = None, end_date: str = None) -> float:
    """Calculate total profit, optionally within a date range (YYYY-MM-DD)."""
    df = get_sales_data()
    if start_date:
        df = df[df['order_date'] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df['order_date'] <= pd.to_datetime(end_date)]
    return round(float(df['profit'].sum()), 2)

def calculate_revenue_by_month() -> List[Dict[str, Any]]:
    """Calculate total revenue aggregated by month."""
    df = get_sales_data()
    df['month'] = df['order_date'].dt.to_period('M')
    monthly = df.groupby('month')['revenue'].sum().reset_index()
    monthly['month'] = monthly['month'].astype(str)
    monthly['revenue'] = monthly['revenue'].round(2)
    return monthly.to_dict(orient='records')

def calculate_profit_by_month() -> List[Dict[str, Any]]:
    """Calculate total profit aggregated by month."""
    df = get_sales_data()
    df['month'] = df['order_date'].dt.to_period('M')
    monthly = df.groupby('month')['profit'].sum().reset_index()
    monthly['month'] = monthly['month'].astype(str)
    monthly['profit'] = monthly['profit'].round(2)
    return monthly.to_dict(orient='records')

def calculate_sales_by_product() -> List[Dict[str, Any]]:
    """Calculate total revenue and profit per product."""
    df = get_sales_data()
    grouped = df.groupby('product_id')[['revenue', 'profit', 'quantity']].sum().reset_index()
    grouped = grouped.round(2)
    return grouped.to_dict(orient='records')

def calculate_sales_by_category() -> List[Dict[str, Any]]:
    """Calculate total revenue and profit per product category."""
    sales = get_sales_data()
    products = get_products_data()
    df = sales.merge(products, on='product_id', how='left')
    grouped = df.groupby('category')[['revenue', 'profit', 'quantity']].sum().reset_index()
    grouped = grouped.round(2)
    return grouped.to_dict(orient='records')

def calculate_sales_by_region() -> List[Dict[str, Any]]:
    """Calculate total revenue and profit per customer region."""
    sales = get_sales_data()
    customers = get_customers_data()
    df = sales.merge(customers, on='customer_id', how='left')
    grouped = df.groupby('location')[['revenue', 'profit', 'quantity']].sum().reset_index()
    grouped = grouped.round(2)
    return grouped.to_dict(orient='records')

def calculate_sales_by_customer_segment() -> List[Dict[str, Any]]:
    """Calculate total revenue and profit per customer segment."""
    sales = get_sales_data()
    customers = get_customers_data()
    df = sales.merge(customers, on='customer_id', how='left')
    grouped = df.groupby('customer_segment')[['revenue', 'profit', 'quantity']].sum().reset_index()
    grouped = grouped.round(2)
    return grouped.to_dict(orient='records')

def compare_period_revenue(start_date: str, end_date: str, comparison_start_date: str, comparison_end_date: str) -> Dict[str, Any]:
    """Compare total revenue between two custom date periods (YYYY-MM-DD)."""
    current_rev = calculate_total_revenue(start_date, end_date)
    prev_rev = calculate_total_revenue(comparison_start_date, comparison_end_date)
    
    change = current_rev - prev_rev
    pct_change = (change / prev_rev * 100) if prev_rev != 0 else 0
    
    return {
        "current_period": f"{start_date} to {end_date}",
        "comparison_period": f"{comparison_start_date} to {comparison_end_date}",
        "current_revenue": current_rev,
        "previous_revenue": prev_rev,
        "absolute_change": round(change, 2),
        "percentage_change": round(pct_change, 2)
    }

def compare_period_profit(start_date: str, end_date: str, comparison_start_date: str, comparison_end_date: str) -> Dict[str, Any]:
    """Compare total profit between two custom date periods (YYYY-MM-DD)."""
    current_profit = calculate_total_profit(start_date, end_date)
    prev_profit = calculate_total_profit(comparison_start_date, comparison_end_date)
    
    change = current_profit - prev_profit
    pct_change = (change / prev_profit * 100) if prev_profit != 0 else 0
    
    return {
        "current_period": f"{start_date} to {end_date}",
        "comparison_period": f"{comparison_start_date} to {comparison_end_date}",
        "current_profit": current_profit,
        "previous_profit": prev_profit,
        "absolute_change": round(change, 2),
        "percentage_change": round(pct_change, 2)
    }
