import os
from agents.llm import get_llm
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from .state import MultiAgentState
from .content_utils import extract_text_content
from .tools_wrapper import (
    compare_customer_activity_between_periods,
    identify_declining_customers
)

CUSTOMER_TOOLS = [
    compare_customer_activity_between_periods,
    identify_declining_customers
]

CUSTOMER_PROMPT = """You are RevPilot's Customer Investigator.

Your job is to investigate whether customer behavior could explain the business change.
Investigate customer revenue, activity, churn, segments, etc.
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

def get_customer_agent():
    llm = get_llm()
    return create_react_agent(llm, tools=CUSTOMER_TOOLS, prompt=CUSTOMER_PROMPT)

def customer_node(state: MultiAgentState):
    """The node function to run the Customer Investigator."""
    try:
        agent = get_customer_agent()
        response = agent.invoke({"messages": [HumanMessage(content=state["user_question"])]})
        final_message = extract_text_content(response["messages"][-1].content)
        
        return {
            "customer_findings": {
                "agent": "customer",
                "findings": final_message
            }
        }
    except Exception as e:
        return {
            "agent_errors": {"customer": str(e)}
        }
