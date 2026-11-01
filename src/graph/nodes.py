
from src.agent import plan_question, _execute_tool


def planner_node(state: dict) -> dict:
    """Create a validated plan using the existing Gemini planner."""

    question = state["question"]

    plan_data = plan_question(question)

    return {
        "planner_source": plan_data["source"],
        "plan": plan_data["steps"],
        "current_step": 0,
        "results": [],
    }


def executor_node(state: dict) -> dict:
    """Execute one approved tool at a time."""

    plan = state["plan"]
    index = state["current_step"]
    question = state["question"]

    if index >= len(plan):
        return {}

    step = plan[index]
    tool_name = step["tool"]

    try:
        output = _execute_tool(tool_name, question)

        result = {
            "tool": tool_name,
            "reason": step["reason"],
            "status": "completed",
            "output": output,
        }

    except Exception as error:
        result = {
            "tool": tool_name,
            "reason": step["reason"],
            "status": "failed",
            "error": str(error),
            "output": None,
        }

    return {
        "results": state.get("results", []) + [result],
        "current_step": index + 1,
    }


def review_node(state: dict) -> dict:
    """Review the execution results."""

    results = state.get("results", [])

    success = any(
        result["status"] == "completed"
        for result in results
    )

    return {
        "success": success,
        "final_report": (
            f"Executed {len(results)} analytical tool(s). "
            f"{sum(r['status'] == 'completed' for r in results)} "
            "completed successfully."
        ),
    }
