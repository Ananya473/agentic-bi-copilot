
from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    question: str

    # Planning information
    planner_source: str
    plan: list[dict]
    current_step: int

    # Tool execution
    results: list[dict]

    # Final review
    success: bool
    final_report: str
