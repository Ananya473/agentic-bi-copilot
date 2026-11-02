
import pandas as pd

from src.agents.supervisor import plan_agents
from src.agents.data_analyst import data_analyst_agent
from src.agents.investigator_agent import investigator_agent
from src.agents.knowledge_researcher import knowledge_researcher_agent
from src.agents.report_agent import report_agent

from src.investigator import (
    analyze_monthly_revenue,
    investigate_revenue_dimension,
)
from src.anomaly_detection import detect_revenue_anomalies


AGENT_FUNCTIONS = {
    "data_analyst": data_analyst_agent,
    "investigator": investigator_agent,
    "knowledge_researcher": knowledge_researcher_agent,
}


def supervisor_node(state: dict) -> dict:
    """Select specialist agents for the business question."""

    question = state["question"]
    plan = plan_agents(question)

    adaptive_mode = any(
        agent.get("agent") == "investigator"
        for agent in plan["agents"]
    )

    return {
        "planner_source": plan["source"],
        "agents_plan": plan["agents"],
        "current_agent": 0,
        "agent_results": [],
        "execution_trace": [],
        "adaptive_mode": adaptive_mode,
        "monthly_analysis": {},
        "country_analysis": {},
        "product_analysis": {},
        "revenue_declined": False,
        "country_investigation_needed": False,
        "product_investigation_needed": False,
        "investigation_decisions": [],
        "anomalies": [],
        "anomaly_rows_analyzed": 0,
        "investigation_errors": {},
    }


def specialist_executor_node(state: dict) -> dict:
    """Execute the next selected specialist agent."""

    index = state["current_agent"]
    plan = state["agents_plan"]

    if index >= len(plan):
        return {}

    selected = plan[index]
    agent_name = selected["agent"]

    if agent_name == "investigator" and state.get("adaptive_mode"):
        return {
            "current_agent": index + 1,
            "execution_trace": (
                state.get("execution_trace", [])
                + ["investigator_deferred_to_adaptive_workflow"]
            ),
        }

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


def monthly_analysis_node(state: dict) -> dict:
    """Analyze monthly revenue and detect anomalies."""

    decisions = state.get("investigation_decisions", [])
    errors = {}
    anomalies = []
    dates_analyzed = 0

    try:
        analysis = analyze_monthly_revenue(state["question"])
        declined = analysis["revenue_change"] < 0

        if declined:
            decision = (
                f"Revenue declined from {analysis['previous_month']} "
                f"to {analysis['current_month']}. "
                "Country investigation is required."
            )
        else:
            decision = (
                f"Revenue did not decline from {analysis['previous_month']} "
                f"to {analysis['current_month']}. "
                "Country and product investigations are not required."
            )

        decisions.append(decision)

    except Exception as error:
        analysis = {"error": str(error)}
        declined = False
        errors["monthly_analysis"] = str(error)
        decisions.append(f"Monthly analysis failed: {error}")

    try:
        anomalies_df = detect_revenue_anomalies()

        if anomalies_df is not None:
            dates_analyzed = len(anomalies_df)

            if not anomalies_df.empty:
                if "is_anomaly" in anomalies_df.columns:
                    unusual_days = anomalies_df[
                        anomalies_df["is_anomaly"] == True
                    ]
                else:
                    unusual_days = anomalies_df

                anomalies = unusual_days.to_dict(orient="records")

        decisions.append("Daily revenue anomaly detection completed.")

    except Exception as error:
        errors["anomaly_detection"] = str(error)
        decisions.append(
            f"Daily revenue anomaly detection failed: {error}"
        )

    return {
        "monthly_analysis": analysis,
        "revenue_declined": declined,
        "country_investigation_needed": declined,
        "anomalies": anomalies,
        "anomaly_rows_analyzed": dates_analyzed,
        "investigation_errors": errors,
        "execution_trace": (
            state.get("execution_trace", []) + ["monthly_analysis"]
        ),
        "investigation_decisions": decisions,
    }


def country_analysis_node(state: dict) -> dict:
    """Investigate country-level revenue changes after a decline."""

    monthly = state["monthly_analysis"]

    try:
        analysis = investigate_revenue_dimension(
            monthly["previous_month"],
            monthly["current_month"],
            "country",
        )

        has_declining_country = (
            analysis.get("largest_decline") is not None
        )

        decision = (
            "Country analysis found a declining country. "
            "Product-level investigation is required."
            if has_declining_country
            else
            "Country analysis found no declining country. "
            "Product-level investigation is not required."
        )

        return {
            "country_analysis": analysis,
            "product_investigation_needed": has_declining_country,
            "execution_trace": (
                state.get("execution_trace", []) + ["country_analysis"]
            ),
            "investigation_decisions": (
                state.get("investigation_decisions", []) + [decision]
            ),
        }

    except Exception as error:
        return {
            "country_analysis": {"error": str(error)},
            "product_investigation_needed": False,
            "execution_trace": (
                state.get("execution_trace", []) + ["country_analysis"]
            ),
            "investigation_decisions": (
                state.get("investigation_decisions", [])
                + [f"Country analysis failed: {error}"]
            ),
        }


def product_analysis_node(state: dict) -> dict:
    """Investigate products when country results justify it."""

    monthly = state["monthly_analysis"]

    try:
        analysis = investigate_revenue_dimension(
            monthly["previous_month"],
            monthly["current_month"],
            "product",
        )

        return {
            "product_analysis": analysis,
            "execution_trace": (
                state.get("execution_trace", []) + ["product_analysis"]
            ),
            "investigation_decisions": (
                state.get("investigation_decisions", [])
                + ["Product-level investigation completed."]
            ),
        }

    except Exception as error:
        return {
            "product_analysis": {"error": str(error)},
            "execution_trace": (
                state.get("execution_trace", []) + ["product_analysis"]
            ),
            "investigation_decisions": (
                state.get("investigation_decisions", [])
                + [f"Product analysis failed: {error}"]
            ),
        }


def report_node(state: dict) -> dict:
    """Combine specialist outputs and adaptive investigation results."""

    agent_results = list(state.get("agent_results", []))

    if state.get("adaptive_mode"):
        monthly = state.get("monthly_analysis", {})
        country = state.get("country_analysis", {})
        product = state.get("product_analysis", {})

        investigator_results = {
            "anomalies": state.get("anomalies", []),
        }

        if monthly and "error" not in monthly:
            revenue_investigation = {
                **monthly,
                "summary": (
                    f"Revenue {monthly['direction']} by "
                    f"{monthly['change_pct']:.2f}% between "
                    f"{monthly['previous_month']} and "
                    f"{monthly['current_month']}."
                ),
                "recommendations": [],
            }

            if country and "error" not in country:
                country_rows = (
                    country.get("declines", [])
                    + country.get("increases", [])
                )
                revenue_investigation["country_drivers"] = (
                    pd.DataFrame(country_rows)
                )

            if product and "error" not in product:
                product_rows = (
                    product.get("declines", [])
                    + product.get("increases", [])
                )
                revenue_investigation["product_drivers"] = (
                    pd.DataFrame(product_rows)
                )

            investigator_results["revenue_investigation"] = (
                revenue_investigation
            )

        agent_results.append({
            "agent": "investigator",
            "status": (
                "completed" if "error" not in monthly else "failed"
            ),
            "results": investigator_results,
            "errors": state.get("investigation_errors", {}),
            "anomaly_rows_analyzed": state.get(
                "anomaly_rows_analyzed", 0
            ),
        })

    result = report_agent(
        question=state["question"],
        planner_source=state["planner_source"],
        agent_results=agent_results,
    )

    final_report = result.get(
        "report",
        result.get("error", "Report generation failed."),
    )

    decisions = state.get("investigation_decisions", [])

    if decisions:
        final_report += "\n\n## Adaptive Investigation Decisions\n"
        final_report += "\n".join(
            f"- {decision}" for decision in decisions
        )

    return {
        "final_report": final_report,
        "report_status": result.get("status", "failed"),
        "agent_results": agent_results,
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
