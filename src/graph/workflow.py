
from langgraph.graph import StateGraph, START, END

from src.graph.state import AgentState
from src.graph.nodes import (
    supervisor_node,
    specialist_executor_node,
    report_node,
    review_node,
)


def route_after_execution(state: AgentState) -> str:
    """Check whether another specialist agent needs to run."""

    if state["current_agent"] < len(state["agents_plan"]):
        return "execute"

    return "report"


def build_workflow():
    """Build the multi-agent business intelligence workflow."""

    graph = StateGraph(AgentState)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("specialist_executor", specialist_executor_node)
    graph.add_node("reporter", report_node)
    graph.add_node("reviewer", review_node)

    graph.add_edge(START, "supervisor")
    graph.add_edge("supervisor", "specialist_executor")

    graph.add_conditional_edges(
        "specialist_executor",
        route_after_execution,
        {
            "execute": "specialist_executor",
            "report": "reporter",
        },
    )

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
