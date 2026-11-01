
from langgraph.graph import StateGraph, START, END

from src.graph.state import AgentState
from src.graph.nodes import (
    planner_node,
    executor_node,
    review_node,
)


def route_after_execution(state: AgentState) -> str:
    """Decide whether another planned tool needs execution."""

    if state["current_step"] < len(state["plan"]):
        return "execute"

    return "review"


def build_workflow():
    """Build the LangGraph business intelligence workflow."""

    graph = StateGraph(AgentState)

    graph.add_node("planner", planner_node)
    graph.add_node("executor", executor_node)
    graph.add_node("reviewer", review_node)

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "executor")

    graph.add_conditional_edges(
        "executor",
        route_after_execution,
        {
            "execute": "executor",
            "review": "reviewer",
        },
    )

    graph.add_edge("reviewer", END)

    return graph.compile()


# Compile the workflow once and reuse it.
agent_workflow = build_workflow()


def run_graph(question: str) -> dict:
    """Run the LangGraph workflow for a business question."""

    if not question or not question.strip():
        raise ValueError("Please enter a business question.")

    initial_state = {
        "question": question.strip(),
        "results": [],
        "current_step": 0,
    }

    return agent_workflow.invoke(initial_state)
