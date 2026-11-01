
from src.agents.supervisor import plan_agents
from src.agents.data_analyst import data_analyst_agent
from src.agents.investigator_agent import investigator_agent
from src.agents.knowledge_researcher import knowledge_researcher_agent
from src.agents.report_agent import report_agent


AGENT_FUNCTIONS = {
    "data_analyst": data_analyst_agent,
    "investigator": investigator_agent,
    "knowledge_researcher": knowledge_researcher_agent,
}


def supervisor_node(state: dict) -> dict:
    """Select specialist agents for the business question."""

    question = state["question"]
    plan = plan_agents(question)

    return {
        "planner_source": plan["source"],
        "agents_plan": plan["agents"],
        "current_agent": 0,
        "agent_results": [],
        "execution_trace": [],
    }


def specialist_executor_node(state: dict) -> dict:
    """Execute the next selected specialist agent."""

    index = state["current_agent"]
    plan = state["agents_plan"]

    if index >= len(plan):
        return {}

    selected = plan[index]
    agent_name = selected["agent"]

    try:
        agent_function = AGENT_FUNCTIONS[agent_name]

        if agent_name == "investigator":
            output = agent_function()
        else:
            output = agent_function(state["question"])

        result = {
            **output,
            "reason": selected.get("reason", ""),
        }

    except Exception as error:
        result = {
            "agent": agent_name,
            "status": "failed",
            "error": str(error),
            "reason": selected.get("reason", ""),
        }

    return {
        "agent_results": state.get("agent_results", []) + [result],
        "execution_trace": (
            state.get("execution_trace", []) + [agent_name]
        ),
        "current_agent": index + 1,
    }


def report_node(state: dict) -> dict:
    """Combine specialist outputs into a final report."""

    result = report_agent(
        question=state["question"],
        planner_source=state["planner_source"],
        agent_results=state.get("agent_results", []),
    )

    return {
        "final_report": result.get(
            "report",
            result.get("error", "Report generation failed."),
        ),
        "report_status": result.get("status", "failed"),
    }


def review_node(state: dict) -> dict:
    """Review specialist execution results."""

    results = state.get("agent_results", [])

    successful = sum(
        result.get("status") == "completed"
        for result in results
    )

    return {
        "success": successful > 0,
        "execution_summary": (
            f"Executed {len(results)} specialist agent(s). "
            f"{successful} completed successfully."
        ),
    }
