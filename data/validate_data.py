import pandas as pd
import json
import os
import sys

def validate_data():
    errors = []
    
    # 1. Check if files exist
    files = [
        'data/raw/products.csv',
        'data/raw/customers.csv',
        'data/raw/sales.csv',
        'data/raw/inventory.csv',
        'data/raw/returns.csv',
        'data/ground_truth/evaluation_cases.json'
    ]
    
    for f in files:
        if not os.path.exists(f):
            errors.append(f"Missing file: {f}")
            
    if errors:
        return errors
        
    # 2. Load data
    products = pd.read_csv('data/raw/products.csv')
    customers = pd.read_csv('data/raw/customers.csv')
    sales = pd.read_csv('data/raw/sales.csv')
    inventory = pd.read_csv('data/raw/inventory.csv')
    returns = pd.read_csv('data/raw/returns.csv')
    
    with open('data/ground_truth/evaluation_cases.json', 'r') as f:
        cases = json.load(f)
        
    # 3. Check for unexpected nulls
    if sales.isnull().any().any():
        errors.append("Null values found in sales.csv")
    if products.isnull().any().any():
        errors.append("Null values found in products.csv")
        
    # 4. Referential integrity
    valid_pids = set(products['product_id'])
    valid_cids = set(customers['customer_id'])
    valid_oids = set(sales['order_id'])
    
    invalid_sales_pids = set(sales['product_id']) - valid_pids
    if invalid_sales_pids:
        errors.append(f"Invalid product IDs in sales: {invalid_sales_pids}")
        
    invalid_sales_cids = set(sales['customer_id']) - valid_cids
    if invalid_sales_cids:
        errors.append(f"Invalid customer IDs in sales: {invalid_sales_cids}")
        
    invalid_returns_oids = set(returns['order_id']) - valid_oids
    if invalid_returns_oids:
        errors.append(f"Invalid order IDs in returns: {invalid_returns_oids}")
        
    # 5. Math consistency
    # revenue = quantity * unit_price * (1 - discount)
    expected_revenue = round(sales['quantity'] * sales['unit_price'] * (1 - sales['discount']), 2)
    revenue_diff = (sales['revenue'] - expected_revenue).abs()
    if (revenue_diff > 0.02).any():
        errors.append("Revenue calculation mismatch in sales.csv")
        
    # profit = revenue - cost
    expected_profit = round(sales['revenue'] - sales['cost'], 2)
    profit_diff = (sales['profit'] - expected_profit).abs()
    if (profit_diff > 0.02).any():
        errors.append("Profit calculation mismatch in sales.csv")
        
    # 6. Evaluation cases check
    if len(cases) < 12:
        errors.append(f"Expected at least 12 evaluation cases, found {len(cases)}")
        
    return errors

if __name__ == "__main__":
    print("Validating dataset...")
    errors = validate_data()
    if errors:
        print("Validation FAILED!")
        for e in errors:
            print(f"- {e}")
        sys.exit(1)
    else:
        print("Validation PASSED! All data is consistent.")
        sys.exit(0)
