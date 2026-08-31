# RevPilot Data Tools

This directory contains the **Tools** that our future AI Agents will use to investigate business data.

## 1. What is a Tool?
In an agentic workflow, an LLM (Large Language Model) cannot do math reliably, nor can it directly read a 30,000-row CSV file. A "Tool" is simply a standard Python function that the LLM is allowed to call. 

The LLM decides *which* tool to call and *what arguments* to pass (like `start_date` and `end_date`), but the tool itself executes purely in Python and returns the factual result to the LLM.

## 2. Why does an agent need tools?
Without tools, an AI is just a chatbot that guesses answers based on its training data. With tools, an AI becomes an **Agent** capable of pulling real-time, factual data from your business systems, running exact calculations, and basing its reasoning on hard evidence.

## 3. Terminology
*   **LLM**: The core "brain" (e.g., GPT-4 or Gemini) that understands text and reasoning.
*   **Tool**: A Python function that performs a specific action (e.g., `calculate_revenue()`).
*   **Agent**: The combination of an LLM equipped with Tools and a system prompt guiding it to solve a goal.

## 4. Tool Modules
*   `data_loader.py`: Handles caching and loading the raw CSV files.
*   `sales_tools.py`: Calculates revenue, profit, and compares periods.
*   `inventory_tools.py`: Investigates stockouts and restock events.
*   `customer_tools.py`: Investigates customer spending and churn.
*   `product_tools.py`: Investigates product-level performance.
*   `returns_tools.py`: Investigates product return rates and quality issues.
*   `registry.py`: A central dictionary of all available tools so the future agent can easily load them.

## 5. Why are these tools deterministic?
These tools do not use AI. If you ask for the revenue of October, the Python code calculates it using standard pandas math. This guarantees that the agent receives 100% accurate, reproducible facts to base its reasoning upon. 

## 6. Why Tools CANNOT Access Ground Truth
Our synthetic dataset comes with an `evaluation_cases.json` file which contains the "answers" to why revenue dropped. If a tool read this file, the agent would just be cheating! The agent must discover the root cause by combining the outputs of the *Data Tools* (e.g., noticing that `compare_period_revenue` went down, and `get_stockout_days` went up).

## 7. Architecture
Here is how the future workflow will look:

```text
Agent (LLM) decides it needs October's revenue
      ↓
Agent calls `compare_period_revenue('2023-10-01', '2023-10-31', ...)`
      ↓
Tool (Python) reads the CSV data and calculates the math
      ↓
Tool returns exact JSON result to Agent
      ↓
Agent (LLM) reads the result and decides what to investigate next
```
