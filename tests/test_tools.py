import pytest
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from tools.sales_tools import calculate_total_revenue, calculate_total_profit, calculate_revenue_by_month, compare_period_revenue
from tools.product_tools import get_product_details, get_product_performance
from tools.inventory_tools import get_stockout_days
from tools.customer_tools import get_customer_revenue
from tools.returns_tools import get_return_rate

def test_calculate_total_revenue():
    # Basic sanity check that it returns a positive float
    rev = calculate_total_revenue()
    assert isinstance(rev, float)
    assert rev > 0

def test_calculate_total_profit():
    # Profit should be a float, maybe negative, but realistically positive here
    profit = calculate_total_profit()
    assert isinstance(profit, float)
    assert profit > 0

def test_monthly_revenue():
    monthly = calculate_revenue_by_month()
    assert isinstance(monthly, list)
    assert len(monthly) == 12 # 12 months in our 2023 dataset
    assert 'month' in monthly[0]
    assert 'revenue' in monthly[0]

def test_period_comparison():
    comp = compare_period_revenue('2023-02-01', '2023-02-28', '2023-01-01', '2023-01-31')
    assert 'current_revenue' in comp
    assert 'absolute_change' in comp
    assert 'percentage_change' in comp

def test_product_performance():
    perf = get_product_performance('P001')
    assert perf['product_id'] == 'P001'
    assert perf['total_orders'] > 0

def test_invalid_product_id():
    with pytest.raises(ValueError):
        get_product_details('INVALID_PROD_123')

def test_inventory_stockout():
    res = get_stockout_days('P001') # We know CASE_01 has stockouts
    assert 'stockout_days' in res
    assert isinstance(res['stockout_days'], int)

def test_customer_revenue():
    # Test valid customer
    res = get_customer_revenue('C0001')
    assert len(res) == 1
    assert res[0]['customer_id'] == 'C0001'

    # Test invalid customer
    with pytest.raises(ValueError):
        get_customer_revenue('INVALID_CUST')

def test_return_rate():
    rate = get_return_rate('P010') # We know P010 has high returns
    assert isinstance(rate, float)
    assert rate >= 0.0
