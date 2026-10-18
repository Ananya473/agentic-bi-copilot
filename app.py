
import streamlit as st
import plotly.express as px

from src.analytics import (
    get_total_revenue,
    get_monthly_revenue,
    get_top_products,
    get_revenue_by_country,
    get_top_customers,
    get_returns_summary,
)
from src.anomaly_detection import detect_revenue_anomalies
from src.question_service import answer_with_sql
from src.investigator import investigate_revenue_change
from src.agent import run_agent
from src.reporting import build_evidence_report
# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Retail BI Copilot",
    page_icon="📊",
    layout="wide",
)

st.title("Retail Business Intelligence Copilot")
st.caption(
    "Retail sales analytics | SQL-powered business questions | "
    "Statistical anomaly detection"
)


# --------------------------------------------------
# Cached data loading
# --------------------------------------------------

@st.cache_data(ttl=60)
def load_dashboard_data():
    return {
        "kpis": get_total_revenue(),
        "monthly": get_monthly_revenue(),
        "products": get_top_products(10),
        "countries": get_revenue_by_country(15),
        "customers": get_top_customers(10),
        "returns": get_returns_summary(),
    }


@st.cache_data(ttl=60)
def load_anomaly_data():
    return detect_revenue_anomalies()
@st.cache_data(ttl=60)
def load_investigation_data():
    return investigate_revenue_change()

# --------------------------------------------------
# Main dashboard
# --------------------------------------------------

try:
    data = load_dashboard_data()

    kpis = data["kpis"].iloc[0]
    monthly = data["monthly"]
    products = data["products"]
    countries = data["countries"]
    customers = data["customers"]
    returns = data["returns"].iloc[0]

    # KPI cards
    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Sales Revenue",
        f"{float(kpis['total_revenue'] or 0):,.2f}",
    )
    col2.metric(
        "Orders",
        f"{int(kpis['total_orders'] or 0):,}",
    )
    col3.metric(
        "Units Sold",
        f"{int(kpis['units_sold'] or 0):,}",
    )
    col4.metric(
        "Unique Customers",
        f"{int(kpis['unique_customers'] or 0):,}",
    )

    st.caption(
        "Revenue uses positive-quantity, positive-price sales rows "
        "excluding invoices beginning with C. Currency is not "
        "converted or explicitly labelled because the dataset "
        "does not provide a currency column."
    )

    st.divider()

    # --------------------------------------------------
    # Monthly revenue trend
    # --------------------------------------------------

    st.subheader("Monthly Revenue Trend")

    if not monthly.empty:
        fig_monthly = px.line(
            monthly,
            x="month",
            y="total_revenue",
            markers=True,
            title="Revenue by Month",
            labels={
                "month": "Month",
                "total_revenue": "Revenue",
            },
        )

        st.plotly_chart(
            fig_monthly,
            use_container_width=True,
        )
    else:
        st.info("No monthly revenue data is available.")

    # --------------------------------------------------
    # Product and country performance
    # --------------------------------------------------

    left, right = st.columns(2)

    with left:
        st.subheader("Top Products by Revenue")

        if not products.empty:
            fig_products = px.bar(
                products.sort_values("total_revenue"),
                x="total_revenue",
                y="product",
                orientation="h",
                hover_data=["stock_code", "units_sold"],
                labels={
                    "total_revenue": "Revenue",
                    "product": "Product",
                },
            )

            st.plotly_chart(
                fig_products,
                use_container_width=True,
            )
        else:
            st.info("No product data is available.")

    with right:
        st.subheader("Top Countries by Revenue")

        if not countries.empty:
            fig_countries = px.bar(
                countries.sort_values("total_revenue"),
                x="total_revenue",
                y="country",
                orientation="h",
                hover_data=["orders", "customers"],
                labels={
                    "total_revenue": "Revenue",
                    "country": "Country",
                },
            )

            st.plotly_chart(
                fig_countries,
                use_container_width=True,
            )
        else:
            st.info("No country-level data is available.")

    st.divider()

    # --------------------------------------------------
    # Customers and returns
    # --------------------------------------------------

    left, right = st.columns(2)

    with left:
        st.subheader("Top Customers")

        if not customers.empty:
            st.dataframe(
                customers,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No customer data is available.")

    with right:
        st.subheader("Returns and Cancellations")

        st.metric(
            "Negative-Quantity Lines",
            f"{int(returns['negative_quantity_lines'] or 0):,}",
        )

        st.metric(
            "Cancelled Invoice Lines",
            f"{int(returns['cancelled_invoice_lines'] or 0):,}",
        )

        st.metric(
            "Negative-Quantity Value (Absolute)",
            f"{float(returns['negative_quantity_value'] or 0):,.2f}",
        )

        st.caption(
            "Negative quantities and cancellation invoice lines "
            "can overlap. Absolute value is not the same as net loss."
        )

    # --------------------------------------------------
    # Revenue anomaly detection
    # --------------------------------------------------

    st.divider()
    st.header("Revenue Anomaly Detection")

    st.write(
        "Identify unusually high or low daily revenue by comparing "
        "each day's revenue with the preceding transaction-active days."
    )

    st.caption(
        "The detector uses a rolling median and median absolute "
        "deviation (MAD), together with a minimum percentage-change "
        "threshold. Flags indicate dates worth investigating; they "
        "do not establish the cause of a change."
    )

    try:
        with st.spinner("Analyzing daily revenue for anomalies..."):
            anomaly_data = load_anomaly_data()

        flagged = anomaly_data[
            anomaly_data["is_anomaly"]
        ].copy()

        high_count = int(
            (flagged["anomaly_type"] == "High revenue").sum()
        )
        low_count = int(
            (flagged["anomaly_type"] == "Low revenue").sum()
        )

        metric1, metric2, metric3 = st.columns(3)

        metric1.metric(
            "Potential Anomalies",
            f"{len(flagged):,}",
        )

        metric2.metric(
            "High-Revenue Flags",
            f"{high_count:,}",
        )

        metric3.metric(
            "Low-Revenue Flags",
            f"{low_count:,}",
        )

        # Actual revenue compared with the historical baseline
        if not anomaly_data.empty:
            fig_anomalies = px.line(
                anomaly_data,
                x="date",
                y=["total_revenue", "expected_revenue"],
                markers=False,
                title="Daily Revenue vs. Historical Baseline",
                labels={
                    "date": "Date",
                    "value": "Revenue",
                    "variable": "Series",
                },
            )

            if not flagged.empty:
                fig_anomalies.add_scatter(
                    x=flagged["date"],
                    y=flagged["total_revenue"],
                    mode="markers",
                    marker={
                        "size": 10,
                        "symbol": "x",
                    },
                    name="Potential anomaly",
                    hovertemplate=(
                        "Date: %{x}<br>"
                        "Actual revenue: %{y:,.2f}"
                        "<extra></extra>"
                    ),
                )

            st.plotly_chart(
                fig_anomalies,
                use_container_width=True,
            )

        if flagged.empty:
            st.info(
                "No potential anomalies were detected "
                "using the current detection settings."
            )
        else:
            st.subheader("Dates Worth Investigating")

            display_data = flagged[
                [
                    "date",
                    "total_revenue",
                    "expected_revenue",
                    "deviation",
                    "deviation_pct",
                    "anomaly_type",
                ]
            ].copy()

            display_data = display_data.sort_values(
                "deviation_pct",
                key=lambda values: values.abs(),
                ascending=False,
            )

            display_data = display_data.rename(
                columns={
                    "date": "Date",
                    "total_revenue": "Actual Revenue",
                    "expected_revenue": "Expected Revenue",
                    "deviation": "Revenue Difference",
                    "deviation_pct": "Difference (%)",
                    "anomaly_type": "Flag",
                }
            )

            numeric_columns = [
                "Actual Revenue",
                "Expected Revenue",
                "Revenue Difference",
                "Difference (%)",
            ]

            display_data[numeric_columns] = display_data[
                numeric_columns
            ].round(2)

            st.dataframe(
                display_data,
                use_container_width=True,
                hide_index=True,
            )

            st.caption(
                "Expected revenue is the historical rolling median. "
                "Investigate flagged dates against order volumes, "
                "products, countries, and possible business events "
                "before drawing conclusions."
            )

    except Exception:
        st.error("Revenue anomaly analysis could not be loaded.")
        st.exception(Exception("Check the anomaly detector and daily analytics."))

    # --------------------------------------------------
    # Multi-step revenue investigation
    # --------------------------------------------------

    st.divider()
    st.header("Multi-Step Revenue Investigation")

    st.write(
        "Investigate monthly revenue changes by comparing overall "
        "performance and examining country- and product-level drivers."
    )

    st.caption(
        "The analysis compares the two latest completed months represented "
        "in the dataset. Findings identify observed associations, not "
        "proven causes."
    )

    if st.button(
        "Investigate Revenue Change",
        type="primary",
        key="run_revenue_investigation",
    ):
        try:
            with st.spinner(
                "Comparing months and investigating country and product performance..."
            ):
                investigation = load_investigation_data()

            st.subheader("Investigation Summary")
            st.write(investigation["summary"])

            # Main revenue comparison
            col1, col2, col3 = st.columns(3)

            col1.metric(
                f"Revenue — {investigation['previous_month']}",
                f"£{investigation['previous_revenue']:,.2f}",
            )

            col2.metric(
                f"Revenue — {investigation['current_month']}",
                f"£{investigation['current_revenue']:,.2f}",
            )

            percentage = investigation["change_pct"]
            percentage_text = (
                f"{percentage:+.1f}%"
                if percentage is not None
                else "Not available"
            )

            col3.metric(
                "Revenue Change",
                f"£{investigation['revenue_change']:+,.2f}",
                delta=percentage_text,
            )

            # Order and unit comparisons
            st.subheader("Supporting Business Metrics")

            comparison = [
                {
                    "Metric": "Distinct orders",
                    "Previous month": investigation["previous_orders"],
                    "Current month": investigation["current_orders"],
                },
                {
                    "Metric": "Units sold",
                    "Previous month": investigation["previous_units"],
                    "Current month": investigation["current_units"],
                },
            ]

            st.dataframe(
                comparison,
                use_container_width=True,
                hide_index=True,
            )

            # Show the analysis steps
            with st.expander("View investigation steps", expanded=False):
                for index, step in enumerate(
                    investigation["steps"], start=1
                ):
                    st.markdown(f"**{index}. {step['step']}**")
                    st.write(step["detail"])

            # Summarize observed findings
            st.subheader("Evidence-Based Findings")

            for finding in investigation["findings"]:
                st.markdown(f"- {finding}")

            # Country-level revenue changes
            country_data = investigation["country_drivers"]

            country_declines = (
                country_data[country_data["change"] < 0]
                .sort_values("change")
                .head(5)
            )

            country_increases = (
                country_data[country_data["change"] > 0]
                .sort_values("change", ascending=False)
                .head(5)
            )

            # Product-level revenue changes
            product_data = investigation["product_drivers"]

            product_declines = (
                product_data[product_data["change"] < 0]
                .sort_values("change")
                .head(5)
            )

            product_increases = (
                product_data[product_data["change"] > 0]
                .sort_values("change", ascending=False)
                .head(5)
            )

            left, right = st.columns(2)

            with left:
                st.subheader("Largest Country Declines")
                if country_declines.empty:
                    st.info("No country-level revenue declines were found.")
                else:
                    st.dataframe(
                        country_declines,
                        use_container_width=True,
                        hide_index=True,
                    )

            with right:
                st.subheader("Largest Country Increases")
                if country_increases.empty:
                    st.info("No country-level revenue increases were found.")
                else:
                    st.dataframe(
                        country_increases,
                        use_container_width=True,
                        hide_index=True,
                    )

            left, right = st.columns(2)

            with left:
                st.subheader("Largest Product Declines")
                if product_declines.empty:
                    st.info("No product-level revenue declines were found.")
                else:
                    st.dataframe(
                        product_declines,
                        use_container_width=True,
                        hide_index=True,
                    )

            with right:
                st.subheader("Largest Product Increases")
                if product_increases.empty:
                    st.info("No product-level revenue increases were found.")
                else:
                    st.dataframe(
                        product_increases,
                        use_container_width=True,
                        hide_index=True,
                    )

            # Chart of the largest absolute country-level movements
            largest_country_moves = (
                country_data.assign(
                    absolute_change=country_data["change"].abs()
                )
                .nlargest(10, "absolute_change")
                .sort_values("change")
            )

            if not largest_country_moves.empty:
                fig_country_moves = px.bar(
                    largest_country_moves,
                    x="change",
                    y="country",
                    orientation="h",
                    title="Largest Country-Level Revenue Changes",
                    labels={
                        "change": "Revenue Change",
                        "country": "Country",
                    },
                )

                st.plotly_chart(
                    fig_country_moves,
                    use_container_width=True,
                )

            # Charts of the largest absolute product-level movements
            largest_product_moves = (
                product_data.assign(
                    absolute_change=product_data["change"].abs()
                )
                .nlargest(10, "absolute_change")
                .sort_values("change")
            )

            if not largest_product_moves.empty:
                fig_product_moves = px.bar(
                    largest_product_moves,
                    x="change",
                    y="product",
                    orientation="h",
                    title="Largest Product-Level Revenue Changes",
                    labels={
                        "change": "Revenue Change",
                        "product": "Product",
                    },
                )

                st.plotly_chart(
                    fig_product_moves,
                    use_container_width=True,
                )

            # Actionable follow-up recommendations
            st.subheader("Recommended Follow-Up Analysis")

            for recommendation in investigation["recommendations"]:
                st.markdown(f"- {recommendation}")

            st.caption(
                "Revenue figures are displayed in GBP, consistent with "
                "the UK retail dataset's currency assumption. Confirm the "
                "currency metadata before using these figures in financial "
                "reporting."
            )

        except Exception as error:
            st.error("The revenue investigation could not be completed.")
            st.exception(error)

    # --------------------------------------------------
    # Natural-language business questions
    # --------------------------------------------------

    st.divider()
    st.header("Ask Your Business Question")

    question = st.text_input(
        "Enter a question about sales, products, customers, or countries",
        placeholder="e.g. Which countries generate the most revenue?",
    )

    if st.button("Analyze", type="primary"):
        if not question.strip():
            st.warning("Please enter a question.")
        else:
            try:
                with st.spinner("Analyzing your question..."):
                    result = answer_with_sql(question)

                st.success("Query executed successfully.")

                st.caption(
                    "SQL generated by: "
                    f"{result.get('source', 'Configured query generator')}"
                )

                st.subheader("Generated SQL")
                st.code(result["sql"], language="sql")

                st.subheader("Query Results")
                st.dataframe(
                    result["data"],
                    use_container_width=True,
                    hide_index=True,
                )

            except ValueError as error:
                st.warning(str(error))

            except Exception as error:
                st.error(
                    "The question could not be processed. "
                    "Check the query generator and SQL execution rules."
                )
                st.exception(error)

    # --------------------------------------------------
    # Agentic Analysis
    # --------------------------------------------------

    st.divider()
    st.header("Agentic Analysis")

    st.write(
        "Ask a business question and let the agent select relevant "
        "analytics tools, execute them, and present the results."
    )

    st.caption(
        "The agent uses a Gemini-based planner when available and "
        "a rule-based fallback when planning fails. Only predefined "
        "analysis tools can be executed."
    )

    agent_question = st.text_input(
        "What would you like the agent to investigate?",
        placeholder=(
            "e.g. Why did revenue change, and were there anomalies?"
        ),
        key="agent_question_input",
    )

    if st.button(
        "Run Agentic Analysis",
        type="primary",
        key="run_agentic_analysis",
    ):
        if not agent_question.strip():
            st.warning("Please enter a business question.")
        else:
            try:
                with st.spinner(
                    "Planning analysis and executing selected tools..."
                ):
                    agent_result = run_agent(agent_question)
                agent_report = build_evidence_report(agent_result)

                with st.expander(
                    "Consolidated Evidence Report",
                    expanded=True,
                ):
                    st.markdown(agent_report)

                    st.download_button(
                        label="Download Report (.md)",
                        data=agent_report,
                        file_name="bi_investigation_report.md",
                        mime="text/markdown",
                        key="download_agent_report",
                    )

                st.subheader("Execution Overview")
                st.caption(
                    f"Planner: {agent_result['planner_source']}"
                )

                if agent_result["success"]:
                    st.success("At least one analysis tool completed.")
                else:
                    st.error("All selected analysis tools failed.")

                st.markdown("**Selected investigation plan**")

                for index, step in enumerate(
                    agent_result["plan"], start=1
                ):
                    st.markdown(
                        f"{index}. **{step['tool']}** — "
                        f"{step['reason']}"
                    )

                st.divider()
                st.subheader("Tool Results")

                for tool_result in agent_result["results"]:
                    tool_name = tool_result["tool"]
                    status = tool_result["status"]
                    output = tool_result.get("output")

                    with st.expander(
                        f"{tool_name} — {status.upper()}",
                        expanded=True,
                    ):
                        if status == "failed":
                            st.error(
                                tool_result.get(
                                    "error", "Unknown tool error."
                                )
                            )
                            continue

                        if tool_name == "answer_question":
                            st.caption(
                                "SQL generation source: "
                                f"{output.get('source', 'Unknown')}"
                            )

                            st.markdown("**Generated SQL**")
                            st.code(output["sql"], language="sql")

                            st.markdown("**Query Results**")
                            query_data = output.get("data")

                            if (
                                query_data is not None
                                and not query_data.empty
                            ):
                                st.dataframe(
                                    query_data,
                                    use_container_width=True,
                                    hide_index=True,
                                )
                            else:
                                st.info("No result rows were returned.")

                        elif tool_name == "investigate_revenue_change":
                            st.markdown("**Investigation Summary**")
                            st.write(output["summary"])

                            col1, col2, col3 = st.columns(3)

                            col1.metric(
                                f"Revenue — {output['previous_month']}",
                                f"{output['previous_revenue']:,.2f}",
                            )

                            col2.metric(
                                f"Revenue — {output['current_month']}",
                                f"{output['current_revenue']:,.2f}",
                            )

                            change_pct = output.get("change_pct")
                            change_label = (
                                f"{change_pct:+.1f}%"
                                if change_pct is not None
                                else "N/A"
                            )

                            col3.metric(
                                "Revenue Change",
                                f"{output['revenue_change']:+,.2f}",
                                delta=change_label,
                            )

                            st.markdown("**Findings to Investigate**")
                            for finding in output["findings"]:
                                st.markdown(f"- {finding}")

                            country_data = output["country_drivers"]
                            product_data = output["product_drivers"]

                            left, right = st.columns(2)

                            with left:
                                st.markdown("**Largest Country Declines**")
                                declines = country_data[
                                    country_data["change"] < 0
                                ].nsmallest(5, "change")

                                st.dataframe(
                                    declines,
                                    use_container_width=True,
                                    hide_index=True,
                                )

                            with right:
                                st.markdown("**Largest Country Increases**")
                                increases = country_data[
                                    country_data["change"] > 0
                                ].nlargest(5, "change")

                                st.dataframe(
                                    increases,
                                    use_container_width=True,
                                    hide_index=True,
                                )

                            left, right = st.columns(2)

                            with left:
                                st.markdown("**Largest Product Declines**")
                                declines = product_data[
                                    product_data["change"] < 0
                                ].nsmallest(5, "change")

                                st.dataframe(
                                    declines,
                                    use_container_width=True,
                                    hide_index=True,
                                )

                            with right:
                                st.markdown("**Largest Product Increases**")
                                increases = product_data[
                                    product_data["change"] > 0
                                ].nlargest(5, "change")

                                st.dataframe(
                                    increases,
                                    use_container_width=True,
                                    hide_index=True,
                                )

                            st.markdown("**Recommended Follow-Up Analysis**")
                            for recommendation in output["recommendations"]:
                                st.markdown(f"- {recommendation}")

                            st.caption(
                                "These are observed associations, not "
                                "proof of business causation."
                            )

                        elif tool_name == "detect_anomalies":
                            st.metric(
                                "Dates Analyzed",
                                f"{output['rows_analyzed']:,}",
                            )

                            st.metric(
                                "Potential Anomalies",
                                f"{output['anomaly_count']:,}",
                            )

                            flagged = output["anomalies"]

                            if flagged.empty:
                                st.info(
                                    "No potential anomalies were detected."
                                )
                            else:
                                st.dataframe(
                                    flagged,
                                    use_container_width=True,
                                    hide_index=True,
                                )

                            st.caption(
                                "Anomaly flags identify dates worth "
                                "investigating; they do not establish causes."
                            )

            except Exception as error:
                st.error("The agentic analysis could not be completed.")
                st.exception(error)


except Exception as error:
    st.error("The dashboard could not load its data.")
    st.exception(error)
