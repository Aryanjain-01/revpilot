import os
from agents.llm import get_llm
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from .state import MultiAgentState
from .content_utils import extract_text_content
from .tools_wrapper import (
    compare_period_revenue,
    compare_period_profit,
    get_product_performance,
    compare_product_performance_between_periods
)

SALES_TOOLS = [
    compare_period_revenue,
    compare_period_profit,
    get_product_performance,
    compare_product_performance_between_periods
]

SALES_PROMPT = """You are RevPilot's Sales Investigator.

Your job is to investigate sales-related evidence.
Do not make unsupported causal claims.
Use deterministic tools for all numerical calculations.
Return structured findings with evidence.
Clearly distinguish:
- observations
- evidence
- hypotheses
- conclusions
Focus conclusions on factual claims that can be verified by deterministic tools.
Do not present correlation as causation.

Do not access ground truth."""

def get_sales_agent():
    llm = get_llm()
    return create_react_agent(llm, tools=SALES_TOOLS, prompt=SALES_PROMPT)

def sales_node(state: MultiAgentState):
    """The node function to run the Sales Investigator."""
    try:
        agent = get_sales_agent()
        # We pass the user question directly to the specialist
        response = agent.invoke({"messages": [HumanMessage(content=state["user_question"])]})
        final_message = extract_text_content(response["messages"][-1].content)
        
        return {
            "sales_findings": {
                "agent": "sales",
                "findings": final_message
            }
        }
    except Exception as e:
        return {
            "agent_errors": {"sales": str(e)}
        }
