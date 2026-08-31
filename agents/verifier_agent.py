import json
from typing import List, Literal

from agents.llm import get_llm
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field

from .content_utils import extract_text_content
from .state import MultiAgentState
from .tools_wrapper import (
    compare_period_revenue,
    compare_period_profit,
    get_stockout_days,
    identify_products_with_high_stockout_frequency,
    compare_customer_activity_between_periods,
    identify_declining_customers,
    get_product_performance,
    identify_products_with_high_return_rates,
    compare_product_performance_between_periods,
)

VerificationClassification = Literal[
    "SUPPORTED",
    "PARTIALLY_SUPPORTED",
    "CONTRADICTED",
    "INSUFFICIENT_EVIDENCE",
]


class VerifiedClaim(BaseModel):
    claim: str = Field(description="The important specialist claim being audited.")
    source_agent: Literal["sales", "inventory", "customer", "unknown"] = Field(
        description="The specialist agent that made the claim."
    )
    classification: VerificationClassification = Field(
        description="How well deterministic tool evidence supports the claim."
    )
    evidence: str = Field(description="Deterministic tool evidence used to assess the claim.")
    verifier_notes: str = Field(
        description="Short explanation, including whether causation was supported or only correlation was observed."
    )


class VerificationReport(BaseModel):
    summary: str = Field(description="Concise summary of the verification audit.")
    verified_claims: List[VerifiedClaim] = Field(
        description="Important specialist claims and their verification classifications."
    )
    unsupported_causal_claims: List[str] = Field(
        default_factory=list,
        description="Claims that imply causation without enough deterministic evidence.",
    )


VERIFIER_TOOLS = [
    compare_period_revenue,
    compare_period_profit,
    get_stockout_days,
    identify_products_with_high_stockout_frequency,
    compare_customer_activity_between_periods,
    identify_declining_customers,
    get_product_performance,
    identify_products_with_high_return_rates,
    compare_product_performance_between_periods,
]

VERIFIER_PROMPT = """You are RevPilot's Evidence Verifier.

Your job is to audit important claims made by specialist agents against deterministic business tools.
Use tools when a claim includes numbers, dates, products, customers, stockouts, returns, revenue, or profit.

Classify each important claim as exactly one of:
- SUPPORTED: deterministic tool evidence directly supports the claim.
- PARTIALLY_SUPPORTED: some parts are supported, but scope, magnitude, or wording is incomplete.
- CONTRADICTED: deterministic tool evidence conflicts with the claim.
- INSUFFICIENT_EVIDENCE: available evidence is missing, ambiguous, or does not establish the claim.

Rules:
1. Do not access ground_truth data, evaluation_cases.json, hidden labels, or hidden evaluation cases.
2. Do not accept causal claims from correlation alone.
3. Reject or downgrade claims that say something caused something else unless deterministic evidence supports causation.
4. Preserve uncertainty clearly.
5. Return structured verification results only.
"""


def build_verification_payload(state: MultiAgentState) -> str:
    """Build the audit packet from specialist findings only."""
    findings = []
    if state.get("sales_findings"):
        findings.append({
            "source_agent": "sales",
            "findings": extract_text_content(state["sales_findings"].get("findings", "")),
        })
    if state.get("inventory_findings"):
        findings.append({
            "source_agent": "inventory",
            "findings": extract_text_content(state["inventory_findings"].get("findings", "")),
        })
    if state.get("customer_findings"):
        findings.append({
            "source_agent": "customer",
            "findings": extract_text_content(state["customer_findings"].get("findings", "")),
        })

    return json.dumps(
        {
            "user_question": state["user_question"],
            "specialist_findings": findings,
            "agent_errors": state.get("agent_errors", {}),
        },
        indent=2,
    )


def get_verifier_agent():
    llm = get_llm()
    return create_react_agent(
        llm,
        tools=VERIFIER_TOOLS,
        prompt=VERIFIER_PROMPT,
        response_format=VerificationReport,
    )


def _empty_report(reason: str) -> dict:
    return VerificationReport(
        summary=reason,
        verified_claims=[],
        unsupported_causal_claims=[],
    ).model_dump()


def verifier_node(state: MultiAgentState):
    """Audit specialist findings before synthesis."""
    if not any([state.get("sales_findings"), state.get("inventory_findings"), state.get("customer_findings")]):
        return {"verification_results": _empty_report("No specialist findings were available to verify.")}

    try:
        agent = get_verifier_agent()
        response = agent.invoke({"messages": [HumanMessage(content=build_verification_payload(state))]})
        report = response.get("structured_response")

        if isinstance(report, VerificationReport):
            verification_results = report.model_dump()
        elif isinstance(report, dict):
            verification_results = VerificationReport.model_validate(report).model_dump()
        else:
            verification_results = _empty_report(
                "Verifier did not return structured results; evidence support is insufficient."
            )

        return {"verification_results": verification_results}
    except Exception as e:
        agent_errors = dict(state.get("agent_errors", {}))
        agent_errors["verifier"] = str(e)
        return {
            "agent_errors": agent_errors,
            "verification_results": _empty_report(
                "Verifier failed before completing the audit; evidence support is insufficient."
            ),
        }
