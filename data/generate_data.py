import os
import json
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Set deterministic seed
np.random.seed(42)
random.seed(42)

def generate_products(num_products=40):
    categories = ['Electronics', 'Home', 'Office', 'Accessories', 'Appliances']
    products = []
    
    for i in range(1, num_products + 1):
        pid = f"P{i:03d}"
        category = random.choice(categories)
        cost = round(random.uniform(10.0, 500.0), 2)
        margin = random.uniform(1.2, 2.5)
        price = round(cost * margin, 2)
        
        products.append({
            "product_id": pid,
            "product_name": f"{category} Item {i}",
            "category": category,
            "cost_price": cost,
            "selling_price": price,
            "launch_date": "2023-01-01",
            "supplier_id": f"S{random.randint(1, 10):03d}"
        })
        
    return pd.DataFrame(products)

def generate_customers(num_customers=750):
    segments = ['Standard', 'Premium', 'Enterprise']
    segment_weights = [0.7, 0.25, 0.05]
    cities = ['Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai', 'Pune']
    
    customers = []
    for i in range(1, num_customers + 1):
        cid = f"C{i:04d}"
        customers.append({
            "customer_id": cid,
            "customer_segment": np.random.choice(segments, p=segment_weights),
            "location": random.choice(cities),
            "signup_date": (datetime(2022, 1, 1) + timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d")
        })
    return pd.DataFrame(customers)

def generate_sales_and_inventory_and_returns(products_df, customers_df):
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 12, 31)
    date_range = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]
    
    sales = []
    inventory = []
    returns = []
    
    # Pre-calculate base demand multipliers
    product_base_demand = {p['product_id']: random.uniform(0.5, 5.0) for _, p in products_df.iterrows()}
    
    order_id_counter = 1
    return_id_counter = 1
    
    # State for inventory tracking
    current_inventory = {p['product_id']: 500 for _, p in products_df.iterrows()}
    
    # Target high-value customers for CASE_02
    premium_customers = customers_df[customers_df['customer_segment'] == 'Enterprise']['customer_id'].tolist()
    churned_customers = premium_customers[:5]
    
    for current_date in date_range:
        month = current_date.month
        is_weekend = current_date.weekday() >= 5
        
        # Daily inventory tracking
        for _, p in products_df.iterrows():
            pid = p['product_id']
            
            # Restock logic (restock to 500 if falls below 50, usually)
            restock_qty = 0
            
            # CASE 01: P001 stockout in September
            if pid == 'P001' and month == 9:
                restock_qty = 0  # No restocks
            # CASE 11: P002 outage in August
            elif pid == 'P002' and month == 8:
                current_inventory[pid] = 0
                restock_qty = 0
            # CASE 08: P025 stockout in June
            elif pid == 'P025' and month == 6:
                restock_qty = 0
            else:
                if current_inventory[pid] < 50:
                    restock_qty = 500 - current_inventory[pid]
                    current_inventory[pid] += restock_qty
            
            inventory.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "product_id": pid,
                "stock_available": current_inventory[pid],
                "stockout": current_inventory[pid] == 0,
                "restock_quantity": restock_qty
            })
            
        # Daily sales generation
        daily_orders_target = int(np.random.normal(50, 10))
        if is_weekend:
            daily_orders_target = int(daily_orders_target * 1.5)
            
        for _ in range(max(1, daily_orders_target)):
            cid = random.choice(customers_df['customer_id'].tolist())
            
            # CASE 02 & CASE 08: Churn
            if cid in churned_customers and month >= 10:
                continue
            if cid == churned_customers[0] and month >= 6: # part of case 08
                continue
                
            cust_info = customers_df[customers_df['customer_id'] == cid].iloc[0]
            
            # CASE 04: Regional Decline in Bangalore from August
            if cust_info['location'] == 'Bangalore' and month >= 8:
                if random.random() < 0.7:  # 70% drop
                    continue
                    
            pid = random.choices(list(product_base_demand.keys()), weights=list(product_base_demand.values()))[0]
            
            # CASE 06: Cannibalization P015 drops because P016 launches in July
            if pid == 'P015' and month >= 7:
                if random.random() < 0.8:
                    pid = 'P016'
            if pid == 'P016' and month < 7:
                continue # P016 doesn't exist yet
                
            # CASE 07: Seasonality P020 only sells well in Nov-Dec
            if pid == 'P020':
                if month not in [11, 12] and random.random() < 0.95:
                    continue
                    
            prod_info = products_df[products_df['product_id'] == pid].iloc[0]
            
            qty = random.randint(1, 5)
            if cust_info['customer_segment'] == 'Enterprise':
                qty *= random.randint(2, 5)
                
            # Check inventory
            if current_inventory[pid] < qty:
                continue # Stockout prevents sale
            
            current_inventory[pid] -= qty
            
            unit_price = prod_info['selling_price']
            cost = prod_info['cost_price']
            discount = 0.05 if cust_info['customer_segment'] in ['Premium', 'Enterprise'] else 0.0
            
            # CASE 03: Discount erosion for P005 in Nov/Dec
            if pid == 'P005' and month in [11, 12]:
                discount = 0.30
                qty *= 2 # Slight volume increase
                
            # CASE 10: Price change for P035 in May (price up 50%, volume down slightly)
            if pid == 'P035':
                if month >= 5:
                    unit_price = round(unit_price * 1.5, 2)
                    if random.random() < 0.3: # 30% volume drop
                        continue
                        
            revenue = qty * unit_price * (1 - discount)
            total_cost = qty * cost
            profit = revenue - total_cost
            
            # CASE 09: Data anomaly - huge duplicate spike in March for P030
            if pid == 'P030' and month == 3 and current_date.day == 15 and random.random() < 0.1:
                qty = 500
                revenue = qty * unit_price * (1 - discount)
                total_cost = qty * cost
                profit = revenue - total_cost
                
            # Record sale
            sales.append({
                "order_id": f"ORD{order_id_counter:06d}",
                "order_date": current_date.strftime("%Y-%m-%d"),
                "customer_id": cid,
                "product_id": pid,
                "quantity": qty,
                "unit_price": unit_price,
                "discount": discount,
                "revenue": round(revenue, 2),
                "cost": round(total_cost, 2),
                "profit": round(profit, 2)
            })
            
            # Returns logic
            return_prob = 0.02
            
            # CASE 05: Returns spike for P010 in Dec
            if pid == 'P010' and month == 12:
                return_prob = 0.40
                
            # CASE 12: False correlation. P038 gets recalled in Oct (huge returns).
            if pid == 'P038' and month == 10:
                return_prob = 0.90
                
            if random.random() < return_prob:
                reasons = ['Damaged', 'Wrong Item', 'Customer Changed Mind', 'Late Delivery']
                if pid == 'P010' and month == 12:
                    reason = 'Quality Issue'
                elif pid == 'P038' and month == 10:
                    reason = 'Quality Issue'
                else:
                    reason = random.choice(reasons)
                    
                returns.append({
                    "return_id": f"RET{return_id_counter:05d}",
                    "return_date": (current_date + timedelta(days=random.randint(1, 10))).strftime("%Y-%m-%d"),
                    "order_id": f"ORD{order_id_counter:06d}",
                    "product_id": pid,
                    "quantity": random.randint(1, qty),
                    "return_reason": reason
                })
                return_id_counter += 1
                
            order_id_counter += 1

    return pd.DataFrame(sales), pd.DataFrame(inventory), pd.DataFrame(returns)

def generate_evaluation_cases():
    cases = [
        {
            "case_id": "CASE_01",
            "title": "Inventory Stockout",
            "business_question": "Why did revenue for P001 decline in September?",
            "expected_root_causes": ["inventory_stockout"],
            "expected_entities": ["P001"],
            "expected_evidence": ["stock_available=0 for P001 in September"],
            "difficulty": "easy",
            "traps": []
        },
        {
            "case_id": "CASE_02",
            "title": "Customer Churn",
            "business_question": "Why did overall Enterprise revenue drop starting in October?",
            "expected_root_causes": ["customer_churn"],
            "expected_entities": ["Enterprise segment"],
            "expected_evidence": ["Top Enterprise customers stopped placing orders in October"],
            "difficulty": "medium",
            "traps": ["Assuming it is a product issue rather than customer churn"]
        },
        {
            "case_id": "CASE_03",
            "title": "Discount Erosion",
            "business_question": "Why did profit for P005 drop in Nov/Dec despite stable/growing revenue?",
            "expected_root_causes": ["excessive_discounting"],
            "expected_entities": ["P005"],
            "expected_evidence": ["discount increased from 0-5% to 30% for P005"],
            "difficulty": "medium",
            "traps": ["Assuming cost price increased"]
        },
        {
            "case_id": "CASE_04",
            "title": "Regional Decline",
            "business_question": "Why did overall sales volume drop slightly from August onwards?",
            "expected_root_causes": ["regional_decline"],
            "expected_entities": ["Bangalore"],
            "expected_evidence": ["70% drop in order frequency from customers located in Bangalore"],
            "difficulty": "medium",
            "traps": []
        },
        {
            "case_id": "CASE_05",
            "title": "Returns Spike",
            "business_question": "Why is the net profitability of P010 so low in December?",
            "expected_root_causes": ["high_returns", "quality_issue"],
            "expected_entities": ["P010"],
            "expected_evidence": ["Return rate for P010 spiked to ~40% due to Quality Issue"],
            "difficulty": "easy",
            "traps": []
        },
        {
            "case_id": "CASE_06",
            "title": "Product Cannibalization",
            "business_question": "Why did sales of P015 plummet in July?",
            "expected_root_causes": ["product_cannibalization"],
            "expected_entities": ["P015", "P016"],
            "expected_evidence": ["P016 launched in July and took over P015's volume"],
            "difficulty": "hard",
            "traps": ["Just saying 'demand dropped' without linking to P016 launch"]
        },
        {
            "case_id": "CASE_07",
            "title": "Seasonality",
            "business_question": "Is the massive drop in sales of P020 in January a cause for concern?",
            "expected_root_causes": ["seasonality"],
            "expected_entities": ["P020"],
            "expected_evidence": ["P020 only sells in Nov-Dec, zero sales in other months"],
            "difficulty": "easy",
            "traps": ["Agent raising false alarm about product death"]
        },
        {
            "case_id": "CASE_08",
            "title": "Multiple Causes",
            "business_question": "Explain the revenue dip for P025 in June.",
            "expected_root_causes": ["inventory_stockout", "customer_churn"],
            "expected_entities": ["P025", "Enterprise customer"],
            "expected_evidence": ["Stockout in June", "Loss of a major customer simultaneously"],
            "difficulty": "hard",
            "traps": ["Stopping investigation after finding only one of the two causes"]
        },
        {
            "case_id": "CASE_09",
            "title": "Data Anomaly",
            "business_question": "What drove the record-breaking revenue spike in March for P030?",
            "expected_root_causes": ["data_anomaly"],
            "expected_entities": ["P030"],
            "expected_evidence": ["Single order with qty 500 on March 15, likely duplicate or error"],
            "difficulty": "medium",
            "traps": ["Inventing a marketing campaign or business reason for the spike"]
        },
        {
            "case_id": "CASE_10",
            "title": "Price Change",
            "business_question": "P035 order volume dropped in May. Was this a negative event for the business?",
            "expected_root_causes": ["strategic_price_increase"],
            "expected_entities": ["P035"],
            "expected_evidence": ["Unit price increased by 50%, profit increased despite 30% volume drop"],
            "difficulty": "hard",
            "traps": ["Assuming volume drop = bad, without checking profit"]
        },
        {
            "case_id": "CASE_11",
            "title": "High-Demand Product Outage",
            "business_question": "Why did August have such low overall revenue?",
            "expected_root_causes": ["inventory_outage"],
            "expected_entities": ["P002"],
            "expected_evidence": ["P002 had 0 stock for the entire month of August"],
            "difficulty": "easy",
            "traps": []
        },
        {
            "case_id": "CASE_12",
            "title": "False Correlation",
            "business_question": "Why did revenue for P038 drop drastically in October?",
            "expected_root_causes": ["quality_issue", "high_returns"],
            "expected_entities": ["P038"],
            "expected_evidence": ["90% return rate for P038 in Oct due to Quality Issue"],
            "difficulty": "hard",
            "traps": ["Blaming missing discounts or generic demand drop without checking returns"]
        }
    ]
    return cases

def main():
    print("Generating synthetic business data...")
    
    os.makedirs('data/raw', exist_ok=True)
    os.makedirs('data/ground_truth', exist_ok=True)
    
    products = generate_products()
    products.to_csv('data/raw/products.csv', index=False)
    print(f"Created products.csv ({len(products)} rows)")
    
    customers = generate_customers()
    customers.to_csv('data/raw/customers.csv', index=False)
    print(f"Created customers.csv ({len(customers)} rows)")
    
    sales, inventory, returns = generate_sales_and_inventory_and_returns(products, customers)
    sales.to_csv('data/raw/sales.csv', index=False)
    print(f"Created sales.csv ({len(sales)} rows)")
    
    inventory.to_csv('data/raw/inventory.csv', index=False)
    print(f"Created inventory.csv ({len(inventory)} rows)")
    
    returns.to_csv('data/raw/returns.csv', index=False)
    print(f"Created returns.csv ({len(returns)} rows)")
    
    cases = generate_evaluation_cases()
    with open('data/ground_truth/evaluation_cases.json', 'w') as f:
        json.dump(cases, f, indent=2)
    print(f"Created evaluation_cases.json ({len(cases)} cases)")
    
    print("Data generation complete!")

if __name__ == "__main__":
    main()
