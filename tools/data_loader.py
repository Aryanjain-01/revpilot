import pandas as pd
import os

# Cache dictionaries to avoid reloading CSVs on every tool call
_CACHE = {}

def _load_csv(filename: str) -> pd.DataFrame:
    """Internal helper to load a CSV and cache it."""
    if filename in _CACHE:
        return _CACHE[filename]
        
    filepath = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Data file {filepath} not found.")
        
    df = pd.read_csv(filepath)
    _CACHE[filename] = df
    return df

def get_sales_data() -> pd.DataFrame:
    """Load sales dataset."""
    df = _load_csv('sales.csv')
    df['order_date'] = pd.to_datetime(df['order_date'])
    return df

def get_products_data() -> pd.DataFrame:
    """Load products dataset."""
    return _load_csv('products.csv')

def get_customers_data() -> pd.DataFrame:
    """Load customers dataset."""
    return _load_csv('customers.csv')

def get_inventory_data() -> pd.DataFrame:
    """Load inventory dataset."""
    df = _load_csv('inventory.csv')
    df['date'] = pd.to_datetime(df['date'])
    return df

def get_returns_data() -> pd.DataFrame:
    """Load returns dataset."""
    df = _load_csv('returns.csv')
    df['return_date'] = pd.to_datetime(df['return_date'])
    return df

def clear_cache():
    """Clear the data cache. Useful for testing."""
    global _CACHE
    _CACHE = {}
