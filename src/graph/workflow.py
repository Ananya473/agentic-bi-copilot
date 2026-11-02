
from langgraph.graph import StateGraph, START, END

from src.graph.state import AgentState
from src.graph.nodes import (
    supervisor_node,
    specialist_executor_node,
    monthly_analysis_node,
    country_analysis_node,
    product_analysis_node,
    report_node,
    review_node,
)


def route_after_supervisor(state: AgentState) -> str:
    """Choose the adaptive or regular workflow."""

    if state.get("adaptive_mode"):
        return "adaptive"

    return "regular"


def route_after_execution(state: AgentState) -> str:
    """Check whether another specialist agent needs to run."""

    if state["current_agent"] < len(state["agents_plan"]):
        return "execute"

    return "report"


def route_after_monthly_analysis(state: AgentState) -> str:
    """Decide whether country-level investigation is necessary."""

    if state.get("country_investigation_needed"):
        return "country"

    return "report"


def route_after_country_analysis(state: AgentState) -> str:
    """Decide whether product-level investigation is necessary."""

    if state.get("product_investigation_needed"):
        return "product"

    return "report"


def build_workflow():
    """Build the adaptive multi-agent BI workflow."""

    graph = StateGraph(AgentState)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("specialist_executor", specialist_executor_node)
    graph.add_node("monthly_analysis", monthly_analysis_node)
    graph.add_node("country_analysis", country_analysis_node)
    graph.add_node("product_analysis", product_analysis_node)
    graph.add_node("reporter", report_node)
    graph.add_node("reviewer", review_node)

    graph.add_edge(START, "supervisor")

    graph.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "adaptive": "monthly_analysis",
            "regular": "specialist_executor",
        },
    )

    graph.add_conditional_edges(
        "specialist_executor",
        route_after_execution,
        {
            "execute": "specialist_executor",
            "report": "reporter",
        },
    )

    graph.add_conditional_edges(
        "monthly_analysis",
        route_after_monthly_analysis,
        {
            "country": "country_analysis",
            "report": "reporter",
        },
    )

    graph.add_conditional_edges(
        "country_analysis",
        route_after_country_analysis,
        {
            "product": "product_analysis",
            "report": "reporter",
        },
    )

    graph.add_edge("product_analysis", "reporter")
    graph.add_edge("reporter", "reviewer")
    graph.add_edge("reviewer", END)

    return graph.compile()


# Compile once and reuse.
agent_workflow = build_workflow()


def run_graph(question: str) -> dict:
    """Run the multi-agent workflow."""

    if not question or not question.strip():
        raise ValueError("Please enter a business question.")

    initial_state = {
        "question": question.strip(),
        "current_agent": 0,
        "agent_results": [],
        "execution_trace": [],
    }

    return agent_workflow.invoke(initial_state)
