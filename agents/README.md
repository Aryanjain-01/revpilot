# RevPilot Agents

This directory contains the AI Agent implementations. We currently support a **Single Agent System** (Step 4), a **Multi-Agent Orchestrator** (Step 5), and an **Evidence Verifier** (Step 6).

## 1. What was a Single-Agent System?
In Step 4, we built a single agent named "RevPilot Analyst." It had access to *all* tools and was responsible for investigating the question, running tools, and writing the final answer. While simple, a single agent can become overwhelmed or confused when given too many tools (e.g. 50+ tools) and complex multi-step problems.

## 2. Why are we introducing Multiple Agents?
Because business problems (like "Why did revenue drop?") have multiple potential causes—sales volume, inventory shortages, customer churn, etc. By creating multiple agents, we allow each one to focus solely on its area of expertise without getting confused by unrelated tools. 

## 3. What Specialization Means
Specialization means restricting an agent's focus and toolset. For instance:
*   **Sales, Inventory, and Customer behavior represent distinct evidence sources.**
*   Separating them allows the **Inventory Agent** to only see inventory tools (`get_stockout_days`). It won't accidentally try to calculate revenue.
*   This makes each LLM more accurate and less prone to hallucinating tool arguments.

## 4. What an Orchestrator Does
The Orchestrator is the "manager." It does not run data tools itself. Its sole job is to read the user's question, determine *which* specialists are needed, and route the question to them. It ensures purposeful execution rather than blindly running every tool.

## 5. What Shared State Does
"State" is the shared memory of the system. In our Multi-Agent system, the state is the "shared investigation notebook." It holds the original question, the Orchestrator's plan, and specific slots for `sales_findings`, `inventory_findings`, and `customer_findings`. As each agent finishes, it writes its findings into this shared notebook.

## 6. Why Specialists Have Different Tools
If an agent only investigates customer churn, it does not need to know how to calculate product return rates. Removing irrelevant tools drastically improves the LLM's accuracy and speeds up its decision-making.

## 7. Why Multiple Specialists May Investigate the Same Question
A drop in revenue is rarely a single isolated event. It might be caused by an inventory shortage (P002 ran out of stock) which led to a high-value customer leaving (Customer churn). Therefore, the orchestrator might ask the Sales, Inventory, and Customer agents to all investigate simultaneously.

## 8. What the Evidence Verifier Does
After all selected specialists finish, the Evidence Verifier audits important specialist claims against deterministic tools. It classifies claims as `SUPPORTED`, `PARTIALLY_SUPPORTED`, `CONTRADICTED`, or `INSUFFICIENT_EVIDENCE`. It does not read `data/ground_truth/evaluation_cases.json` or any hidden labels. It also downgrades unsupported causal claims when the evidence only shows observation or correlation.

## 9. What Synthesis Does
After verification, the Synthesis node reads the shared notebook and the verifier report. It prioritizes verified evidence, compares the findings, acknowledges uncertainty, and drafts the final answer without presenting unsupported causation as fact.

## 10. Difference Between Components
*   **Orchestrator**: Decides *who* should work on the problem.
*   **Specialist Agent**: An LLM focused on one specific domain (e.g., Sales), allowed to decide *which* tools to use to find evidence.
*   **Evidence Verifier**: Audits important claims using deterministic tools and classifies evidence support.
*   **Tool**: A dumb, deterministic Python script that calculates factual math.
*   **Synthesis**: An LLM step that reads the verified reports and writes the final summary.

## 11. Why This Architecture is Still Incomplete
We are still missing a **Decision** node and what-if simulation. The current system can investigate, verify evidence, and synthesize an answer, but it does not yet recommend business actions or simulate interventions.

## Multi-Agent Architecture Diagram

```text
User
 ↓
Orchestrator (Manager)
 ↓
┌──────────┬─────────────┬───────────┐
↓          ↓             ↓
Sales   Inventory     Customer
Agent     Agent         Agent
└──────────┴─────────────┴───────────┘
              ↓
       Evidence Verifier
              ↓
           Synthesis (Combines findings)
              ↓
            Answer
```
