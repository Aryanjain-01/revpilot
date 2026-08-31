import pytest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from agents.state import MultiAgentState
from agents.orchestrator import create_multi_agent_graph, route_agents
from agents.sales_agent import SALES_TOOLS
from agents.inventory_agent import INVENTORY_TOOLS
from agents.customer_agent import CUSTOMER_TOOLS
from agents.verifier_agent import (
    VERIFIER_TOOLS,
    VerificationReport,
    build_verification_payload,
    verifier_node,
)
from agents.decision_agent import (
    DecisionReport,
    build_decision_payload,
    decision_node,
)

def test_multi_agent_state_initialization():
    """Test that our MultiAgentState TypedDict state structure works as expected."""
    state = MultiAgentState(
        user_question="Test question",
        messages=[],
        investigation_plan={},
        active_agent="",
        sales_findings={},
        inventory_findings={},
        customer_findings={},
        agent_errors={},
        verification_results={},
        decision_result={},
        final_answer=""
    )
    assert state['user_question'] == "Test question"
    assert isinstance(state['messages'], list)

def test_sales_agent_tool_restrictions():
    """Verify Sales Agent only has access to relevant tools."""
    tool_names = [tool.name for tool in SALES_TOOLS]
    assert "compare_period_revenue" in tool_names
    assert "get_stockout_days" not in tool_names

def test_inventory_agent_tool_restrictions():
    """Verify Inventory Agent only has access to relevant tools."""
    tool_names = [tool.name for tool in INVENTORY_TOOLS]
    assert "get_stockout_days" in tool_names
    assert "compare_period_revenue" not in tool_names

def test_customer_agent_tool_restrictions():
    """Verify Customer Agent only has access to relevant tools."""
    tool_names = [tool.name for tool in CUSTOMER_TOOLS]
    assert "identify_declining_customers" in tool_names
    assert "get_stockout_days" not in tool_names

def test_verifier_has_cross_domain_tools_without_ground_truth():
    """Verifier can audit claims with deterministic tools only."""
    tool_names = [tool.name for tool in VERIFIER_TOOLS]
    assert "compare_period_revenue" in tool_names
    assert "compare_period_profit" in tool_names
    assert "get_stockout_days" in tool_names
    assert "identify_declining_customers" in tool_names
    assert all("ground_truth" not in name for name in tool_names)
    assert all("evaluation_cases" not in name for name in tool_names)

def test_verifier_classifications_are_supported():
    report = VerificationReport(
        summary="All classifications are valid.",
        verified_claims=[
            {
                "claim": classification,
                "source_agent": "sales",
                "classification": classification,
                "evidence": "mocked deterministic evidence",
                "verifier_notes": "mocked verifier note",
            }
            for classification in [
                "SUPPORTED",
                "PARTIALLY_SUPPORTED",
                "CONTRADICTED",
                "INSUFFICIENT_EVIDENCE",
            ]
        ],
        unsupported_causal_claims=["Revenue drop was caused by churn."],
    )
    assert [claim.classification for claim in report.verified_claims] == [
        "SUPPORTED",
        "PARTIALLY_SUPPORTED",
        "CONTRADICTED",
        "INSUFFICIENT_EVIDENCE",
    ]

def test_orchestrator_routing():
    """Test the conditional routing logic of the orchestrator."""
    state = MultiAgentState(investigation_plan={"selected_agents": ["sales", "inventory"]})
    destinations = route_agents(state)
    assert "sales" in destinations
    assert "inventory" in destinations
    assert "customer" not in destinations

def test_orchestrator_routes_empty_plan_to_verifier():
    """Even empty specialist plans pass through verifier before synthesis."""
    state = MultiAgentState(investigation_plan={"selected_agents": []})
    assert route_agents(state) == ["verifier"]

def test_build_verification_payload_uses_specialist_findings_only():
    state = MultiAgentState(
        user_question="Did profit change?",
        sales_findings={"findings": "Revenue fell 1%; this may correlate with profit."},
        inventory_findings={},
        customer_findings={},
        agent_errors={},
    )
    payload = build_verification_payload(state)
    assert "Revenue fell 1%" in payload
    assert "evaluation_cases" not in payload
    assert "ground_truth" not in payload

def test_verifier_node_accepts_mocked_structured_response(monkeypatch):
    """Verifier integration should not require a real Gemini API call in tests."""
    report = VerificationReport(
        summary="Revenue and profit claims checked.",
        verified_claims=[
            {
                "claim": "Revenue fell from September to October.",
                "source_agent": "sales",
                "classification": "SUPPORTED",
                "evidence": "compare_period_revenue returned a negative change.",
                "verifier_notes": "Observation supported; no causal claim made.",
            }
        ],
        unsupported_causal_claims=[],
    )

    class FakeVerifierAgent:
        def invoke(self, _inputs):
            return {"structured_response": report}

    monkeypatch.setattr("agents.verifier_agent.get_verifier_agent", lambda: FakeVerifierAgent())
    state = MultiAgentState(
        user_question="Did profit change differently from revenue?",
        sales_findings={"findings": "Revenue fell and profit fell less."},
        inventory_findings={},
        customer_findings={},
        agent_errors={},
    )

    result = verifier_node(state)
    assert result["verification_results"]["summary"] == "Revenue and profit claims checked."
    assert result["verification_results"]["verified_claims"][0]["classification"] == "SUPPORTED"

def test_build_decision_payload_uses_only_verification_results():
    state = MultiAgentState(
        user_question="Do not include this",
        sales_findings={"findings": "Do not include this finding"},
        verification_results={
            "summary": "Verified revenue changed.",
            "verified_claims": [],
            "unsupported_causal_claims": [],
        },
        agent_errors={},
    )
    payload = build_decision_payload(state)
    assert "Verified revenue changed." in payload
    assert "Do not include this" not in payload
    assert "ground_truth" not in payload
    assert "evaluation_cases" not in payload

def test_decision_node_accepts_mocked_structured_response(monkeypatch):
    """Decision Agent tests should not call Gemini."""
    report = DecisionReport(
        primary_driver="Profit declined less than revenue based on supported verifier evidence.",
        confidence=0.72,
        recommended_actions=["Review margin mix changes using verified sales evidence."],
    )

    class FakeDecisionLLM:
        def invoke(self, _messages):
            return report

    monkeypatch.setattr("agents.decision_agent.get_decision_llm", lambda: FakeDecisionLLM())
    state = MultiAgentState(
        verification_results={
            "summary": "Revenue and profit comparisons are supported.",
            "verified_claims": [
                {
                    "claim": "Profit declined less than revenue.",
                    "source_agent": "sales",
                    "classification": "SUPPORTED",
                    "evidence": "mocked deterministic evidence",
                    "verifier_notes": "observation only",
                }
            ],
            "unsupported_causal_claims": [],
        },
        agent_errors={},
    )

    result = decision_node(state)
    assert result["decision_result"]["primary_driver"] == report.primary_driver
    assert result["decision_result"]["confidence"] == 0.72
    assert result["decision_result"]["recommended_actions"] == report.recommended_actions

def test_decision_node_low_confidence_without_verification_results():
    result = decision_node(MultiAgentState(verification_results={}))
    assert result["decision_result"]["confidence"] == 0.0
    assert "Insufficient verified evidence" in result["decision_result"]["primary_driver"]

def test_multi_agent_graph_construction():
    """Test that the LangGraph compiles successfully for multi-agent setup."""
    original_key = os.environ.get("GEMINI_API_KEY")
    if not original_key:
        os.environ["GEMINI_API_KEY"] = "fake-key-for-testing"
        
    try:
        app = create_multi_agent_graph()
        assert app is not None
        assert hasattr(app, "invoke")
    finally:
        if not original_key and "GEMINI_API_KEY" in os.environ:
            del os.environ["GEMINI_API_KEY"]
