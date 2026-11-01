
from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    # User input
    question: str

    # Supervisor planning
    planner_source: str
    agents_plan: list[dict]
    current_agent: int

    # Specialist agent outputs
    agent_results: list[dict]

    # Execution tracking
    execution_trace: list[str]
    success: bool

    # Final report
    final_report: str
    report_status: str
    execution_summary: str