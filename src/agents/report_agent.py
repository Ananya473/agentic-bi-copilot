
import pandas as pd

from src.reporting import build_evidence_report


AGENT_RESPONSIBILITIES = {
    "data_analyst": "SQL queries and business data analysis",
    "investigator": "Revenue investigation and anomaly detection",
    "knowledge_researcher": "Business knowledge retrieval using RAG",
}


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

    # ------------------------------------------
    # Agent execution summary
    # ------------------------------------------

    execution_lines = [
        "## Agent Execution Summary",
        "",
    ]

    for item in agent_results:
        agent = item.get("agent", "unknown")
        status = item.get("status", "failed")

        responsibility = AGENT_RESPONSIBILITIES.get(
            agent,
            "Business intelligence task",
        )

        execution_lines.append(
            f"- **{agent.replace('_', ' ').title()}** "
            f"({responsibility}): {status.title()}"
        )

        # --------------------------------------
        # Data Analyst
        # --------------------------------------

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
                    "error": item.get(
                        "error",
                        "Data Analyst failed.",
                    ),
                })

        # --------------------------------------
        # Investigator
        # --------------------------------------

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

        # --------------------------------------
        # Knowledge Researcher (RAG)
        # --------------------------------------

        elif agent == "knowledge_researcher":
            if status == "completed":
                documents = item.get(
                    "retrieved_documents", []
                )
                sources = item.get("sources", [])

                knowledge_sections.extend([
                    "",
                    "## Business Knowledge Research",
                    "",
                    "### Research Answer",
                    "",
                    item.get(
                        "answer",
                        "No answer was generated.",
                    ),
                    "",
                    "### Retrieved Evidence",
                    "",
                ])

                if documents:
                    for index, document in enumerate(
                        documents,
                        start=1,
                    ):
                        knowledge_sections.extend([
                            f"#### Document {index}: "
                            f"{document.get('source', 'Unknown source')}",
                            "",
                            f"**Category:** "
                            f"{document.get('category', 'General')}",
                            "",
                        ])

                        distance = document.get("distance")

                        if isinstance(distance, (int, float)):
                            knowledge_sections.extend([
                                f"**ChromaDB distance:** {distance:.4f}",
                                "",
                            ])

                        knowledge_sections.extend([
                            "**Retrieved content:**",
                            "",
                            document.get(
                                "document",
                                "No document content available.",
                            ),
                            "",
                        ])

                else:
                    knowledge_sections.append(
                        "No retrieved document excerpts were provided."
                    )

                    # Backward compatibility:
                    # Include source filenames even if excerpts are absent.
                    if sources:
                        knowledge_sections.extend([
                            "",
                            "**Retrieved document sources:**",
                            "",
                        ])

                        knowledge_sections.extend(
                            f"- {source}" for source in sources
                        )

            else:
                knowledge_sections.extend([
                    "",
                    "## Business Knowledge Research",
                    "",
                    "Research could not be completed: "
                    + item.get("error", "Unknown error."),
                ])

    # ------------------------------------------
    # Build the existing evidence report
    # ------------------------------------------

    report_input = {
        "question": question.strip(),
        "planner_source": planner_source,
        "results": normalized_results,
    }

    try:
        report = build_evidence_report(report_input)

        # Insert additional sections after the title
        # and business question, before detailed findings.
        report_parts = report.split(
            "## Execution Summary",
            1,
        )

        if len(report_parts) == 2:
            report = (
                report_parts[0]
                + "\n".join(execution_lines)
                + "\n"
                + "\n".join(knowledge_sections)
                + "\n\n"
                + "## Detailed Evidence and Findings\n\n"
                + report_parts[1]
            )

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
