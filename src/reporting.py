
import numbers

import pandas as pd


def _format_value(value) -> str:
    """Format scalar values for a readable report."""
    if value is None:
        return "N/A"

    try:
        if pd.isna(value):
            return "N/A"
    except (TypeError, ValueError):
        pass

    if isinstance(value, numbers.Integral):
        return f"{value:,}"

    if isinstance(value, numbers.Real):
        return f"{value:,.2f}"

    return str(value)


def _append_top_changes(
    lines: list[str],
    title: str,
    data: pd.DataFrame,
    dimension: str,
    positive: bool,
    limit: int = 3,
) -> None:
    """Append the largest increases or decreases observed in a DataFrame."""

    lines.append(f"\n### {title}")

    if (
        data is None
        or data.empty
        or dimension not in data.columns
        or "change" not in data.columns
    ):
        lines.append("No supporting comparison data is available.")
        return

    candidates = data[data["change"] > 0] if positive else data[data["change"] < 0]

    candidates = candidates.sort_values(
        "change",
        ascending=not positive,
    ).head(limit)

    if candidates.empty:
        lines.append("No changes of this type were found.")
        return

    for _, row in candidates.iterrows():
        previous = row.get("previous_revenue")
        current = row.get("current_revenue")
        change = row["change"]

        detail = (
            f"- **{row[dimension]}:** revenue change "
            f"{float(change):+,.2f}"
        )

        if previous is not None and current is not None:
            detail += (
                f" (from {_format_value(previous)} "
                f"to {_format_value(current)})"
            )

        lines.append(detail)


def build_evidence_report(agent_result: dict) -> str:
    """
    Build a deterministic Markdown report from completed agent tool outputs.

    The report summarizes returned evidence. It does not infer that a
    correlation or change proves a business cause.
    """

    if not isinstance(agent_result, dict):
        raise ValueError("agent_result must be a dictionary.")

    question = agent_result.get("question", "Not provided")
    planner = agent_result.get("planner_source", "Unknown")
    results = agent_result.get("results", [])

    lines = [
        "# Business Intelligence Investigation Report",
        "",
        f"**Business question:** {question}",
        f"**Planning method:** {planner}",
        "",
        "## Execution Summary",
    ]

    completed = [
        item for item in results
        if item.get("status") == "completed"
    ]
    failed = [
        item for item in results
        if item.get("status") != "completed"
    ]

    lines.append(f"- Tools completed: {len(completed)}")
    lines.append(f"- Tools failed: {len(failed)}")

    if failed:
        lines.append("\n### Tool Errors")
        for item in failed:
            lines.append(
                f"- **{item.get('tool', 'Unknown tool')}:** "
                f"{item.get('error', 'No error details provided.')}"
            )

    for item in completed:
        tool = item.get("tool")
        output = item.get("output") or {}

        if tool == "investigate_revenue_change":
            lines.extend([
                "",
                "## Revenue Change Investigation",
                "",
                str(output.get("summary", "No summary available.")),
                "",
                "### Supporting Monthly Metrics",
                (
                    f"- {output.get('previous_month', 'Previous month')}: "
                    f"revenue {_format_value(output.get('previous_revenue'))}, "
                    f"{_format_value(output.get('previous_orders'))} orders, "
                    f"{_format_value(output.get('previous_units'))} units sold"
                ),
                (
                    f"- {output.get('current_month', 'Current month')}: "
                    f"revenue {_format_value(output.get('current_revenue'))}, "
                    f"{_format_value(output.get('current_orders'))} orders, "
                    f"{_format_value(output.get('current_units'))} units sold"
                ),
            ])

            countries = output.get("country_drivers")
            products = output.get("product_drivers")

            if isinstance(countries, pd.DataFrame):
                _append_top_changes(
                    lines,
                    "Largest Country Revenue Declines",
                    countries,
                    "country",
                    positive=False,
                )
                _append_top_changes(
                    lines,
                    "Largest Country Revenue Increases",
                    countries,
                    "country",
                    positive=True,
                )

            if isinstance(products, pd.DataFrame):
                _append_top_changes(
                    lines,
                    "Largest Product Revenue Declines",
                    products,
                    "product",
                    positive=False,
                )
                _append_top_changes(
                    lines,
                    "Largest Product Revenue Increases",
                    products,
                    "product",
                    positive=True,
                )

            recommendations = output.get("recommendations", [])
            lines.append("\n### Suggested Follow-Up Checks")

            if recommendations:
                for recommendation in recommendations:
                    lines.append(f"- {recommendation}")
            else:
                lines.append("No follow-up checks were provided.")

        elif tool == "detect_anomalies":
            flagged = output.get("anomalies")

            lines.extend([
                "",
                "## Revenue Anomaly Results",
                "",
                f"- Dates analyzed: {_format_value(output.get('rows_analyzed'))}",
                f"- Potential anomalies: {_format_value(output.get('anomaly_count'))}",
            ])

            if isinstance(flagged, pd.DataFrame) and not flagged.empty:
                ordered = flagged.copy()

                if "deviation_pct" in ordered.columns:
                    ordered = ordered.reindex(
                        ordered["deviation_pct"].abs()
                        .sort_values(ascending=False)
                        .index
                    )

                lines.append("\n### Largest Flagged Deviations")

                for _, row in ordered.head(5).iterrows():
                    lines.append(
                        f"- **{row.get('date', 'Unknown date')}** — "
                        f"{row.get('anomaly_type', 'Potential anomaly')}; "
                        f"actual revenue {_format_value(row.get('total_revenue'))}; "
                        f"baseline {_format_value(row.get('expected_revenue'))}; "
                        f"deviation {_format_value(row.get('deviation_pct'))}%"
                    )

            lines.append(
                "\nThese flags identify dates for further investigation. "
                "They do not establish why the revenue movement occurred."
            )

        elif tool == "answer_question":
            lines.extend([
                "",
                "## Business Query Results",
            ])

            source = output.get("source", "Unknown")
            lines.append(f"- SQL generation source: {source}")

            query = output.get("sql")
            if query:
                lines.extend([
                    "",
                    "**Executed SQL**",
                    "",
                    "```sql",
                    str(query).strip(),
                    "```",
                ])

            frame = output.get("data")

            if isinstance(frame, pd.DataFrame):
                lines.append(
                    f"\nReturned rows: {len(frame):,}"
                )

                if frame.empty:
                    lines.append("The query returned no rows.")
                else:
                    lines.append("\n### Sample Results")
                    for _, row in frame.head(5).iterrows():
                        fields = [
                            f"{column}: {_format_value(value)}"
                            for column, value in row.items()
                        ]
                        lines.append("- " + "; ".join(fields))

                    if len(frame) > 5:
                        lines.append(
                            f"- Showing 5 of {len(frame):,} returned rows."
                        )

    lines.extend([
        "",
        "## Interpretation and Limitations",
        "",
        "- Findings summarize the actual outputs returned by the selected tools.",
        "- Revenue changes by country or product are descriptive comparisons, "
        "not proof of causation.",
        "- Potential anomalies require further business investigation.",
        "- Recommendations are suggested follow-up checks, not verified root causes.",
    ])

    return "\n".join(lines)
