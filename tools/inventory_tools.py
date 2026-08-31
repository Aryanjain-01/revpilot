import pandas as pd
from typing import Dict, List, Any
from .data_loader import get_inventory_data, get_products_data

def get_stockout_summary() -> List[Dict[str, Any]]:
    """Return a summary of total stockout days per product."""
    df = get_inventory_data()
    stockouts = df[df['stockout'] == True]
    summary = stockouts.groupby('product_id').size().reset_index(name='stockout_days')
    return summary.to_dict(orient='records')

def get_product_inventory_history(product_id: str) -> List[Dict[str, Any]]:
    """Get the full daily inventory history for a specific product."""
    df = get_inventory_data()
    product_df = df[df['product_id'] == product_id]
    if product_df.empty:
        raise ValueError(f"No inventory records found for product_id: {product_id}")
    
    # Convert dates to string for JSON serialization
    product_df = product_df.copy()
    product_df['date'] = product_df['date'].dt.strftime('%Y-%m-%d')
    return product_df.to_dict(orient='records')

def get_stockout_days(product_id: str) -> Dict[str, Any]:
    """Return the number of stockout days for a product and the relevant dates."""
    df = get_inventory_data()
    product_df = df[(df['product_id'] == product_id) & (df['stockout'] == True)]
    
    if product_df.empty:
        return {
            "product_id": product_id,
            "stockout_days": 0,
            "first_stockout": None,
            "last_stockout": None,
            "evidence": []
        }
        
    dates = product_df['date'].dt.strftime('%Y-%m-%d').tolist()
    return {
        "product_id": product_id,
        "stockout_days": len(dates),
        "first_stockout": dates[0],
        "last_stockout": dates[-1],
        "evidence": product_df[['date', 'stock_available']].assign(date=lambda x: x['date'].dt.strftime('%Y-%m-%d')).to_dict(orient='records')
    }

def get_inventory_by_date_range(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """Get all inventory records within a specific date range."""
    df = get_inventory_data()
    mask = (df['date'] >= pd.to_datetime(start_date)) & (df['date'] <= pd.to_datetime(end_date))
    filtered_df = df[mask].copy()
    filtered_df['date'] = filtered_df['date'].dt.strftime('%Y-%m-%d')
    return filtered_df.to_dict(orient='records')

def identify_products_with_high_stockout_frequency(threshold_days: int = 5) -> List[Dict[str, Any]]:
    """Find products that have been out of stock for more than `threshold_days`."""
    summary = get_stockout_summary()
    return [item for item in summary if item['stockout_days'] >= threshold_days]

def get_restock_events(product_id: str) -> List[Dict[str, Any]]:
    """Get a list of dates and quantities when a product was restocked."""
    df = get_inventory_data()
    events = df[(df['product_id'] == product_id) & (df['restock_quantity'] > 0)].copy()
    events['date'] = events['date'].dt.strftime('%Y-%m-%d')
    return events[['date', 'restock_quantity']].to_dict(orient='records')
