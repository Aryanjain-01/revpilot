import pytest
import os
import sys

# Insert project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from data.validate_data import validate_data
from data.generate_data import generate_products, generate_customers, generate_sales_and_inventory_and_returns
import pandas as pd
import numpy as np
import random

def test_data_validation():
    # Run the validation function to ensure referential integrity and math
    errors = validate_data()
    assert len(errors) == 0, f"Data validation failed with errors: {errors}"

def test_deterministic_generation():
    # Test if regenerating produces the same rows (using the same seed)
    np.random.seed(42)
    random.seed(42)
    p1 = generate_products()
    c1 = generate_customers()
    s1, _, _ = generate_sales_and_inventory_and_returns(p1, c1)
    
    np.random.seed(42)
    random.seed(42)
    p2 = generate_products()
    c2 = generate_customers()
    s2, _, _ = generate_sales_and_inventory_and_returns(p2, c2)
    
    pd.testing.assert_frame_equal(s1, s2)
    
def test_revenue_and_profit_calculations():
    # Load actual data to spot check math
    sales = pd.read_csv('data/raw/sales.csv')
    
    # Pick a random row
    row = sales.iloc[10]
    
    expected_revenue = round(row['quantity'] * row['unit_price'] * (1 - row['discount']), 2)
    assert abs(row['revenue'] - expected_revenue) < 0.02
    
    expected_profit = round(row['revenue'] - row['cost'], 2)
    assert abs(row['profit'] - expected_profit) < 0.02
