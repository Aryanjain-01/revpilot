import os
from typing import Annotated, Literal
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

# Import our deterministic tools
from tools.registry import AVAILABLE_TOOLS
from .state import AgentState
from .prompts import ANALYST_SYSTEM_PROMPT

from .tools_wrapper import (
    compare_period_revenue,
    compare_period_profit,
    get_stockout_days,
    identify_products_with_high_stockout_frequency,
    compare_customer_activity_between_periods,
    identify_declining_customers,
    get_product_performance,
    identify_products_with_high_return_rates,
    compare_product_performance_between_periods
)

# List of tools to expose to the LLM
AGENT_TOOLS = [
    compare_period_revenue,
    compare_period_profit,
    get_stockout_days,
    identify_products_with_high_stockout_frequency,
    compare_customer_activity_between_periods,
    identify_declining_customers,
    get_product_performance,
    identify_products_with_high_return_rates,
    compare_product_performance_between_periods
]

# --- BUILD THE LANGGRAPH WORKFLOW ---

from agents.llm import get_llm

def create_agent_graph():
    """Create and return the LangGraph executable application."""
    
    # 1. Initialize the LLM
    llm = get_llm()
    
    # Bind the tools to the LLM so it knows it can call them
    llm_with_tools = llm.bind_tools(AGENT_TOOLS)
    
    # 2. Define the node functions
    def call_model(state: AgentState):
        """Call the LLM to get the next step or final answer."""
        messages = state['messages']
        
        # If this is the first run, ensure the system prompt is present
        if len(messages) == 1 and isinstance(messages[0], HumanMessage):
            messages = [SystemMessage(content=ANALYST_SYSTEM_PROMPT)] + list(messages)
            
        response = llm_with_tools.invoke(messages)
        
        # Update the state with the new message
        return {"messages": [response]}
        
    # The ToolNode automatically executes the tools requested by the LLM
    tool_node = ToolNode(AGENT_TOOLS)
    
    # 3. Define routing logic
    def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
        """Decide whether to call a tool or end the workflow."""
        last_message = state['messages'][-1]
        # If the LLM made a tool call, route to the 'tools' node
        if last_message.tool_calls:
            return "tools"
        # Otherwise, the LLM has finished its investigation
        return "__end__"
        
    # 4. Construct the Graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)
    
    # Set entry point
    workflow.add_edge(START, "agent")
    
    # Add conditional edges from the agent node
    workflow.add_conditional_edges("agent", should_continue)
    
    # Add normal edge from tools back to agent
    workflow.add_edge("tools", "agent")
    
    return workflow.compile()
