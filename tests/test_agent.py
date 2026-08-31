import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from agents.state import AgentState
from agents.analyst_agent import AGENT_TOOLS, create_agent_graph
from agents.content_utils import extract_text_content
import agents.tools_wrapper as tools_wrapper
from langchain_core.messages import HumanMessage
from pydantic import ValidationError

def test_state_creation():
    """Test that our TypedDict state structure works as expected."""
    state = AgentState(
        user_question="Test question",
        messages=[HumanMessage(content="Test question")],
        final_answer=""
    )
    assert state['user_question'] == "Test question"
    assert len(state['messages']) == 1

def test_tool_registration():
    """Test that all expected tools are exposed to the agent."""
    tool_names = [tool.name for tool in AGENT_TOOLS]
    assert "compare_period_revenue" in tool_names
    assert "get_stockout_days" in tool_names
    assert len(AGENT_TOOLS) >= 5
    
def test_invalid_tool_input():
    """Test that the tool wrapper catches invalid inputs."""
    # Finding the compare_period_revenue tool
    tool = next(t for t in AGENT_TOOLS if t.name == "compare_period_revenue")
    
    # Missing required argument
    with pytest.raises(ValidationError):
        tool.invoke({"start_date": "2023-01-01"})

def test_tool_invocation():
    """Test invoking a wrapped tool directly without the LLM."""
    tool = next(t for t in AGENT_TOOLS if t.name == "get_stockout_days")
    result = tool.invoke({"product_id": "P001"})
    
    # Should return a dictionary from the underlying tool
    assert isinstance(result, dict)
    assert "stockout_days" in result

def test_extract_text_content_removes_gemini_metadata():
    """Gemini text parts should not expose metadata/signatures."""
    content = [
        {
            "type": "text",
            "text": "Visible answer",
            "extras": {"signature": "do-not-print"},
        }
    ]
    assert extract_text_content(content) == "Visible answer"

def test_reversed_period_comparison_uses_cached_result(monkeypatch):
    """A swapped date-range comparison should not rerun deterministic business logic."""
    calls = []

    def fake_compare(start_date, end_date, comparison_start_date, comparison_end_date):
        calls.append((start_date, end_date, comparison_start_date, comparison_end_date))
        return {
            "current_period": f"{start_date} to {end_date}",
            "comparison_period": f"{comparison_start_date} to {comparison_end_date}",
            "current_revenue": 100.0,
            "previous_revenue": 80.0,
            "absolute_change": 20.0,
            "percentage_change": 25.0,
        }

    tools_wrapper._COMPARISON_CACHE.clear()
    monkeypatch.setitem(tools_wrapper.AVAILABLE_TOOLS, "compare_period_revenue", fake_compare)

    tool = next(t for t in AGENT_TOOLS if t.name == "compare_period_revenue")
    first = tool.invoke({
        "start_date": "2023-09-01",
        "end_date": "2023-09-30",
        "comparison_start_date": "2023-10-01",
        "comparison_end_date": "2023-10-31",
    })
    second = tool.invoke({
        "start_date": "2023-10-01",
        "end_date": "2023-10-31",
        "comparison_start_date": "2023-09-01",
        "comparison_end_date": "2023-09-30",
    })

    assert len(calls) == 1
    assert first["absolute_change"] == 20.0
    assert second["current_revenue"] == 80.0
    assert second["previous_revenue"] == 100.0
    assert second["absolute_change"] == -20.0

def test_agent_graph_construction():
    """Test that the LangGraph compiles successfully."""
    # Requires setting a dummy Gemini key if not present just for compilation.
    original_key = os.environ.get("GEMINI_API_KEY")
    if not original_key:
        os.environ["GEMINI_API_KEY"] = "fake-key-for-testing"
        
    try:
        app = create_agent_graph()
        assert app is not None
        assert hasattr(app, "invoke")
    finally:
        # Restore environment
        if not original_key and "GEMINI_API_KEY" in os.environ:
            del os.environ["GEMINI_API_KEY"]

@pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="Requires GEMINI_API_KEY")
def test_full_agent_execution():
    """
    Integration test for the full agent workflow. 
    Only runs if an API key is provided.
    """
    app = create_agent_graph()
    inputs = {
        "user_question": "What is 2+2?",
        "messages": [HumanMessage(content="What is 2+2? Do not use tools.")]
    }
    result = app.invoke(inputs)
    assert len(result["messages"]) > 1
