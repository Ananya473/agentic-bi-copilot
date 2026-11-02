from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    question: str

    # Supervisor planning
    planner_source: str
    agents_plan: list[dict]
    current_agent: int

    # Agent execution
    agent_results: list[dict]
    execution_trace: list[str]
    success: bool

    # Analysis results
    monthly_analysis: dict
    country_analysis: dict
    product_analysis: dict

    # Adaptive investigation decisions
    revenue_declined: bool
    country_investigation_needed: bool
    product_investigation_needed: bool
    investigation_decisions: list[str]
    adaptive_mode: bool

    # Anomaly detection
    anomalies: list[dict]
    anomaly_rows_analyzed: int

    # Error tracking
    investigation_errors: dict

    # Final report
    final_report: str
    report_status: str
    execution_summary: str