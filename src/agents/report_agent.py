
import pandas as pd

from src.reporting import build_evidence_report


def report_agent(
    question: str,
    planner_source: str,
    agent_results: list[dict],
) -> dict:
    """
    Report Agent:
    Combines specialist agent outputs into one
    evidence-based business intelligence report.
    """

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    if not isinstance(agent_results, list):
        raise ValueError("agent_results must be a list.")

    normalized_results = []
    knowledge_sections = []

    for item in agent_results:
        agent = item.get("agent")
        status = item.get("status", "failed")

        if agent == "data_analyst":
            if status == "completed":
                normalized_results.append({
                    "tool": "answer_question",
                    "status": "completed",
                    "output": item.get("result", {}),
                })
            else:
                normalized_results.append({
                    "tool": "answer_question",
                    "status": "failed",
                    "error": item.get("error", "Data Analyst failed."),
                })

        elif agent == "investigator":
            results = item.get("results", {})

            revenue = results.get("revenue_investigation")
            if revenue is not None:
                normalized_results.append({
                    "tool": "investigate_revenue_change",
                    "status": "completed",
                    "output": revenue,
                })

            anomalies = results.get("anomalies", [])
            anomalies_df = pd.DataFrame(anomalies)

            if "is_anomaly" not in anomalies_df.columns:
                anomalies_df["is_anomaly"] = True

            normalized_results.append({
                "tool": "detect_anomalies",
                "status": "completed",
                "output": {
                    "anomalies": anomalies_df,
                    "anomaly_count": len(anomalies_df),
                },
            })

            for name, error in item.get("errors", {}).items():
                normalized_results.append({
                    "tool": name,
                    "status": "failed",
                    "error": error,
                })

            if status == "failed" and not results:
                normalized_results.append({
                    "tool": "investigator",
                    "status": "failed",
                    "error": "Investigator could not produce results.",
                })

        elif agent == "knowledge_researcher":
            if status == "completed":
                sources = item.get("sources", [])
                knowledge_sections.extend([
                    "",
                    "## Business Knowledge Research",
                    "",
                    item.get("answer", "No answer was generated."),
                    "",
                    "**Retrieved document sources:**",
                ])

                if sources:
                    knowledge_sections.extend(
                        f"- {source}" for source in sources
                    )
                else:
                    knowledge_sections.append(
                        "No source filenames were provided."
                    )
            else:
                knowledge_sections.extend([
                    "",
                    "## Business Knowledge Research",
                    "",
                    "Research could not be completed: "
                    + item.get("error", "Unknown error."),
                ])

    report_input = {
        "question": question.strip(),
        "planner_source": planner_source,
        "results": normalized_results,
    }

    try:
        report = build_evidence_report(report_input)

        if knowledge_sections:
            report += "\n" + "\n".join(knowledge_sections)

        return {
            "agent": "report_agent",
            "status": "completed",
            "question": question,
            "report": report,
            "agents_used": [
                item.get("agent")
                for item in agent_results
            ],
        }

    except Exception as error:
        return {
            "agent": "report_agent",
            "status": "failed",
            "question": question,
            "error": str(error),
        }
