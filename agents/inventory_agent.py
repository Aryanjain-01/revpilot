import os
from agents.llm import get_llm
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from .state import MultiAgentState
from .content_utils import extract_text_content
from .tools_wrapper import (
    get_stockout_days,
    identify_products_with_high_stockout_frequency
)

INVENTORY_TOOLS = [
    get_stockout_days,
    identify_products_with_high_stockout_frequency
]

INVENTORY_PROMPT = """You are RevPilot's Inventory Investigator.

Your job is to investigate whether inventory constraints could explain the observed business change.
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

def get_inventory_agent():
    llm = get_llm()
    return create_react_agent(llm, tools=INVENTORY_TOOLS, prompt=INVENTORY_PROMPT)

def inventory_node(state: MultiAgentState):
    """The node function to run the Inventory Investigator."""
    try:
        agent = get_inventory_agent()
        response = agent.invoke({"messages": [HumanMessage(content=state["user_question"])]})
        final_message = extract_text_content(response["messages"][-1].content)
        
        return {
            "inventory_findings": {
                "agent": "inventory",
                "findings": final_message
            }
        }
    except Exception as e:
        return {
            "agent_errors": {"inventory": str(e)}
        }
