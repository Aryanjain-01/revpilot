import json
from typing import List

from agents.llm import get_llm
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from .state import MultiAgentState


class DecisionReport(BaseModel):
    primary_driver: str = Field(
        description="The most likely driver based only on verified evidence, or a clear insufficiency statement."
    )
    confidence: float = Field(
        ge=0,
        le=1,
        description="Confidence from 0 to 1 based only on verified evidence quality.",
    )
    recommended_actions: List[str] = Field(
        description="Small set of actions grounded in verified evidence."
    )


DECISION_PROMPT = """You are RevPilot's lightweight Decision Agent.

You receive ONLY the Evidence Verifier results. Do not use specialist findings, raw data, hidden labels, ground_truth data, or evaluation_cases.json.

Rules:
1. Base the decision only on verified evidence in the provided verification_results.
2. Never invent numbers or evidence.
3. Do not claim causation unless supported by verified evidence.
4. If evidence is insufficient, say so in primary_driver and use low confidence.
5. Keep recommended actions practical and tied to verified evidence.
"""


def build_decision_payload(state: MultiAgentState) -> str:
    """Build the decision input from verification results only."""
    return json.dumps(
        {
            "verification_results": state.get("verification_results", {}),
        },
        indent=2,
    )


def get_decision_llm():
    return get_llm().with_structured_output(DecisionReport)


def _fallback_decision(reason: str) -> dict:
    return DecisionReport(
        primary_driver=reason,
        confidence=0.0,
        recommended_actions=["Collect or verify more evidence before making a decision."],
    ).model_dump()


def decision_node(state: MultiAgentState):
    """Choose a lightweight decision from verifier output only."""
    if not state.get("verification_results"):
        return {
            "decision_result": _fallback_decision(
                "Insufficient verified evidence to identify a primary driver."
            )
        }

    try:
        decision_llm = get_decision_llm()
        decision = decision_llm.invoke([
            SystemMessage(content=DECISION_PROMPT),
            HumanMessage(content=build_decision_payload(state)),
        ])

        if isinstance(decision, DecisionReport):
            decision_result = decision.model_dump()
        elif isinstance(decision, dict):
            decision_result = DecisionReport.model_validate(decision).model_dump()
        else:
            decision_result = _fallback_decision(
                "Decision Agent did not return structured output from verified evidence."
            )

        return {"decision_result": decision_result}
    except Exception as e:
        agent_errors = dict(state.get("agent_errors", {}))
        agent_errors["decision"] = str(e)
        return {
            "agent_errors": agent_errors,
            "decision_result": _fallback_decision(
                "Decision Agent failed; insufficient verified evidence to identify a primary driver."
            ),
        }
