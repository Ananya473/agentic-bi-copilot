
import pandas as pd

from src.reporting import build_evidence_report


AGENT_RESPONSIBILITIES = {
    "data_analyst": "SQL queries and business data analysis",
    "investigator": "Revenue investigation and anomaly detection",
    "knowledge_researcher": "Business knowledge retrieval using RAG",
}


def format_anomaly_details(anomalies_df: pd.DataFrame) -> str:
    """Format detected revenue anomalies as a readable Markdown table."""

    if anomalies_df.empty:
        return "No unusual daily revenue patterns were detected."

    required_columns = [
        "date",
        "total_revenue",
        "expected_revenue",
        "deviation_pct",
        "anomaly_type",
    ]

    available_columns = [
        column for column in required_columns
        if column in anomalies_df.columns
    ]

    if not available_columns:
        return "Anomaly details were unavailable."

    details = anomalies_df[available_columns].copy()

    lines = [
        "| Date | Actual Revenue | Expected Revenue | Deviation | Type |",
        "|---|---:|---:|---:|---|",
    ]

    for _, row in details.iterrows():
        date = row.get("date", "Unknown")
        actual = row.get("total_revenue")
        expected = row.get("expected_revenue")
        deviation = row.get("deviation_pct")
        anomaly_type = row.get("anomaly_type", "Unknown")

        actual_text = (
            f"{actual:,.2f}"
            if pd.notna(actual) else "N/A"
        )
        expected_text = (
            f"{expected:,.2f}"
            if pd.notna(expected) else "N/A"
        )
        deviation_text = (
            f"{deviation:+.2f}%"
            if pd.notna(deviation) else "N/A"
        )

        lines.append(
            f"| {date} | {actual_text} | {expected_text} "
            f"| {deviation_text} | {anomaly_type} |"
        )

    return "\n".join(lines)


def report_agent(
    question: str,
    planner_source: str,
    agent_results: list[dict],
) -> dict:
    """Combine specialist outputs into an evidence-based report."""

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    if not isinstance(agent_results, list):
        raise ValueError("agent_results must be a list.")

    normalized_results = []
    knowledge_sections = []
    anomaly_details = None

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
            errors = item.get("errors", {})

            revenue = results.get("revenue_investigation")

            if revenue is not None:
                normalized_results.append({
                    "tool": "investigate_revenue_change",
                    "status": "completed",
                    "output": revenue,
                })

            if "anomalies" in results:
                anomalies_df = pd.DataFrame(results["anomalies"])

                if "is_anomaly" not in anomalies_df.columns:
                    anomalies_df["is_anomaly"] = True

                if not anomalies_df.empty:
                    anomalies_df = anomalies_df[
                        anomalies_df["is_anomaly"].fillna(False)
                    ].copy()

                anomaly_details = format_anomaly_details(
                    anomalies_df
                )

                analyzed_count = item.get(
                    "anomaly_rows_analyzed", 0
                )

                normalized_results.append({
                    "tool": "detect_anomalies",
                    "status": "completed",
                    "output": {
                        "anomalies": anomalies_df,
                        "anomaly_count": len(anomalies_df),
                        "rows_analyzed": analyzed_count,
                        "dates_analyzed": analyzed_count,
                    },
                })

            elif "anomaly_detection" in errors:
                normalized_results.append({
                    "tool": "detect_anomalies",
                    "status": "failed",
                    "error": errors["anomaly_detection"],
                })

            for name, error in errors.items():
                if name != "anomaly_detection":
                    normalized_results.append({
                        "tool": name,
                        "status": "failed",
                        "error": error,
                    })

            if status == "failed" and not results:
                normalized_results.append({
                    "tool": "investigator",
                    "status": "failed",
                    "error": item.get(
                        "error",
                        "Investigator could not produce results.",
                    ),
                })

        elif agent == "knowledge_researcher":
            if status == "completed":
                documents = item.get("retrieved_documents", [])
                sources = item.get("sources", [])

                knowledge_sections.extend([
                    "",
                    "## Business Knowledge Research",
                    "",
                    "### Research Answer",
                    "",
                    item.get("answer", "No answer was generated."),
                    "",
                    "### Retrieved Evidence",
                    "",
                ])

                if documents:
                    for index, document in enumerate(
                        documents, start=1
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

    report_input = {
        "question": question.strip(),
        "planner_source": planner_source,
        "results": normalized_results,
    }

    try:
        report = build_evidence_report(report_input)

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

        if anomaly_details is not None:
            anomaly_section = (
                "\n\n### Individual Anomaly Details\n\n"
                + anomaly_details
                + "\n"
            )

            marker = "## Interpretation and Limitations"

            if marker in report:
                report = report.replace(
                    marker,
                    anomaly_section + "\n" + marker,
                    1,
                )
            else:
                report += (
                    "\n\n## Individual Anomaly Details\n\n"
                    + anomaly_details
                    + "\n"
                )

        return {
            "agent": "report_agent",
            "status": "completed",
            "question": question,
            "report": report,
            "agents_used": [
                item.get("agent") for item in agent_results
            ],
        }

    except Exception as error:
        return {
            "agent": "report_agent",
            "status": "failed",
            "question": question,
            "error": str(error),
        }
