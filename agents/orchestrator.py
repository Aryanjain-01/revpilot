import os
from typing import List, Literal
from agents.llm import get_llm
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from .state import MultiAgentState
from .sales_agent import sales_node
from .inventory_agent import inventory_node
from .customer_agent import customer_node
from .verifier_agent import verifier_node
from .decision_agent import decision_node
from .content_utils import extract_text_content

class InvestigationPlan(BaseModel):
    selected_agents: List[Literal["sales", "inventory", "customer"]] = Field(
        description="The agents selected to investigate the root cause of the business issue."
    )
    reason: str = Field(description="Why these specific agents were selected.")

ORCHESTRATOR_PROMPT = """You are the RevPilot Orchestrator.
Your job is to analyze the user's business question and decide which specialist agents need to investigate.
You do not perform the analysis yourself. You are the manager.

Available Specialists:
- "sales": Analyzes revenue changes, profit changes, and product performance.
- "inventory": Analyzes stockouts, restocks, and availability issues.
- "customer": Analyzes customer behavior, churn, and high-value customer activity.

Rules:
1. Select only the necessary agents.
2. If the question involves a broad revenue drop, it is often best to select multiple agents (e.g., sales, inventory, and customer) as any could be the root cause.
3. For highly specific questions (e.g. "Did stockouts affect P002?"), select only the relevant agents (e.g., inventory and sales).
"""

def orchestrator_node(state: MultiAgentState):
    """The manager that decides which agents to route to."""
    llm = get_llm()
    structured_llm = llm.with_structured_output(InvestigationPlan)
    
    messages = [
        SystemMessage(content=ORCHESTRATOR_PROMPT),
        HumanMessage(content=state["user_question"])
    ]
    
    plan: InvestigationPlan = structured_llm.invoke(messages)
    
    return {
        "investigation_plan": plan.dict()
    }

def route_agents(state: MultiAgentState):
    """Conditional edge router that returns a list of agent nodes to run in parallel."""
    plan = state.get("investigation_plan", {})
    selected = plan.get("selected_agents", [])
    
    destinations = []
    if "sales" in selected:
        destinations.append("sales")
    if "inventory" in selected:
        destinations.append("inventory")
    if "customer" in selected:
        destinations.append("customer")
        
    # If LLM failed to select any, still verify the empty notebook before synthesis
    if not destinations:
        destinations.append("verifier")
        
    return destinations

SYNTHESIS_PROMPT = """You are the Synthesis Agent.
You receive the findings from specialized investigation agents (Sales, Inventory, Customer) and the original user question.
You also receive an Evidence Verifier report that audited important claims against deterministic tools.
You also receive a lightweight Decision Agent report based only on verified evidence.

Your job:
1. Prioritize VERIFIED evidence over unverified specialist statements.
2. Use the Decision Agent report as guidance, but do not overstate it.
3. Summarize the findings.
4. Identify possible root causes only when supported by verified evidence.
5. Compare evidence.
6. Acknowledge uncertainty when claims are PARTIALLY_SUPPORTED, CONTRADICTED, or INSUFFICIENT_EVIDENCE.
7. Avoid claiming causation without sufficient verified evidence.

If an agent failed or its findings are missing, acknowledge that limitation.
"""

def synthesis_node(state: MultiAgentState):
    """Aggregates findings into a final preliminary answer."""
    llm = get_llm()
    
    content = f"Original Question: {state['user_question']}\n\n"
    
    if state.get("agent_errors"):
        content += f"Errors encountered during investigation: {state['agent_errors']}\n\n"

    if state.get("verification_results"):
        content += f"--- Evidence Verification ---\n{state['verification_results']}\n\n"

    if state.get("decision_result"):
        content += f"--- Decision Agent Report ---\n{state['decision_result']}\n\n"
        
    if state.get("sales_findings"):
        content += f"--- Sales Findings ---\n{extract_text_content(state['sales_findings'].get('findings'))}\n\n"
        
    if state.get("inventory_findings"):
        content += f"--- Inventory Findings ---\n{extract_text_content(state['inventory_findings'].get('findings'))}\n\n"
        
    if state.get("customer_findings"):
        content += f"--- Customer Findings ---\n{extract_text_content(state['customer_findings'].get('findings'))}\n\n"
        
    if not any([state.get("sales_findings"), state.get("inventory_findings"), state.get("customer_findings")]):
        content += "No findings were produced by the specialists."
        
    messages = [
        SystemMessage(content=SYNTHESIS_PROMPT),
        HumanMessage(content=content)
    ]
    
    response = llm.invoke(messages)
    
    return {
        "final_answer": extract_text_content(response.content)
    }

def create_multi_agent_graph():
    """Build the multi-agent graph."""
    workflow = StateGraph(MultiAgentState)
    
    # Add nodes
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("sales", sales_node)
    workflow.add_node("inventory", inventory_node)
    workflow.add_node("customer", customer_node)
    workflow.add_node("verifier", verifier_node)
    workflow.add_node("decision_agent", decision_node)
    workflow.add_node("synthesis", synthesis_node)
    
    # Set entry point
    workflow.add_edge(START, "orchestrator")
    
    # Conditional routing from orchestrator to specialists (can run in parallel)
    workflow.add_conditional_edges(
        "orchestrator",
        route_agents,
        ["sales", "inventory", "customer", "verifier"]
    )
    
    # Once specialists finish, they all go to verification
    workflow.add_edge("sales", "verifier")
    workflow.add_edge("inventory", "verifier")
    workflow.add_edge("customer", "verifier")
    workflow.add_edge("verifier", "decision_agent")
    workflow.add_edge("decision_agent", "synthesis")
    
    # Synthesis ends the graph
    workflow.add_edge("synthesis", END)
    
    return workflow.compile()
