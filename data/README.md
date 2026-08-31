# RevPilot Data Environment

This directory contains synthetic business data and evaluation ground truth for testing the RevPilot multi-agent system.

## 1. Available Datasets

The data is separated into `raw/` which contains the business data, and `ground_truth/` which contains the answers to the hidden scenarios.

**`data/raw/`**
- `products.csv`: ~40 products with costs, prices, categories.
- `customers.csv`: ~750 customers across different segments and locations.
- `sales.csv`: ~30,000 order records across 12 months with calculated revenue, cost, and profit.
- `inventory.csv`: Daily inventory snapshots and restock events.
- `returns.csv`: Return records tied to specific orders and products.

## 2. Generating the Data

We use deterministic generation to create a reliable evaluation dataset that includes hidden business scenarios (e.g. stockouts, cannibalization, seasonality).

To regenerate the dataset, run:
```bash
python data/generate_data.py
```

## 3. Validating the Data

To ensure referential integrity and math consistency, run:
```bash
python data/validate_data.py
```

## 4. Ground Truth & Evaluation

**IMPORTANT:** The file `data/ground_truth/evaluation_cases.json` contains the hidden root causes for anomalies in the dataset. 

**DO NOT** expose this file to the LangGraph agents during their investigation phase. It exists *solely* for the final evaluation script to grade the agent's conclusions against the known facts.
