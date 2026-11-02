
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
from src.graph.workflow import run_graph
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
    # Multi-Agent Analysis using LangGraph
    # --------------------------------------------------

    st.divider()
    st.header("Multi-Agent Business Intelligence")

    st.write(
        "Ask a business question and let a Supervisor coordinate "
        "specialist AI agents to analyze your retail data and "
        "business knowledge."
    )

    st.caption(
        "Powered by LangGraph, Gemini, SQL analytics and "
        "Retrieval-Augmented Generation (RAG)."
    )
    
    # Agent Workflow Architecture
    with st.expander("View Multi-Agent Architecture", expanded=True):
        workflow_diagram = """
        digraph AgentWorkflow {
            rankdir=TB;
            graph [bgcolor="transparent", nodesep=0.45, ranksep=0.55];
            node [shape=box, style="rounded,filled",
                  fontname="Arial", color="#64748b"];
            edge [color="#64748b"];

            User [label="User Question", fillcolor="#dbeafe"];
            Supervisor [label="Supervisor\\nGemini Planning", fillcolor="#ede9fe"];
            Monthly [label="Monthly Revenue\\nAnalysis", fillcolor="#d1fae5"];
            Decision [label="Revenue Declined?", shape=diamond, fillcolor="#fef3c7"];
            Country [label="Country-Level\\nInvestigation", fillcolor="#d1fae5"];
            CountryDecision [label="Declining Country Found?", shape=diamond, fillcolor="#fef3c7"];
            Product [label="Product-Level\\nInvestigation", fillcolor="#d1fae5"];
            Anomaly [label="Daily Revenue\\nAnomaly Detection", fillcolor="#d1fae5"];
            Reporter [label="Report Agent\\nEvidence Consolidation", fillcolor="#fde68a"];
            Reviewer [label="Reviewer", fillcolor="#e0e7ff"];
            Output [label="Final BI Report", fillcolor="#e0e7ff"];

            User -> Supervisor;
            Supervisor -> Monthly;
            Monthly -> Decision;
            Decision -> Country [label="Yes"];
            Decision -> Anomaly [label="No"];
            Country -> CountryDecision;
            CountryDecision -> Product [label="Yes"];
            CountryDecision -> Anomaly [label="No"];
            Product -> Anomaly;
            Anomaly -> Reporter;
            Reporter -> Reviewer;
            Reviewer -> Output;
        }
        """

        st.graphviz_chart(workflow_diagram, use_container_width=True)


    agent_question = st.text_input(
        "What would you like the AI team to investigate?",
        placeholder=(
            "e.g. Why did revenue decline, and could promotions "
            "explain it?"
        ),
        key="agent_question_input",
    )

    if st.button(
        "Run Multi-Agent Analysis",
        type="primary",
        key="run_agentic_analysis",
    ):
        if not agent_question.strip():
            st.warning("Please enter a business question.")

        else:
            try:
                with st.spinner(
                    "Supervisor is planning and coordinating specialist agents..."
                ):
                    agent_result = run_graph(agent_question)

                # ------------------------------------------
                # Execution overview
                # ------------------------------------------

                st.subheader("Execution Overview")

                st.caption(
                    f"Supervisor planning method: "
                    f"{agent_result.get('planner_source', 'Unknown')}"
                )

                if agent_result.get("success"):
                    st.success(
                        agent_result.get(
                            "execution_summary",
                            "At least one specialist completed successfully.",
                        )
                    )
                else:
                    st.error(
                        agent_result.get(
                            "execution_summary",
                            "No specialist completed successfully.",
                        )
                    )
                
                # ------------------------------------------
                # Agent Execution Tracker
                # ------------------------------------------

                st.subheader("Agent Execution Tracker")

                selected_agents = {
                    item.get("agent")
                    for item in agent_result.get("agents_plan", [])
                }

                executed_results = {
                    item.get("agent"): item
                    for item in agent_result.get("agent_results", [])
                }

                agent_details = [
                    ("Supervisor", "Task planning", "completed"),
                    ("Data Analyst", "SQL queries", "data_analyst"),
                    ("Investigator", "Adaptive revenue and anomaly analysis", "investigator"),
                    ("Knowledge Researcher", "RAG and document retrieval", "knowledge_researcher"),
                ]

                tracker_rows = []

                for name, responsibility, agent_key in agent_details:
                    if agent_key == "completed":
                        status = "Completed"
                    elif agent_key not in selected_agents:
                        status = "Not selected"
                    else:
                        result = executed_results.get(agent_key, {})
                        status = result.get("status", "pending").title()

                    tracker_rows.append({
                        "Agent": name,
                        "Responsibility": responsibility,
                        "Execution Status": status,
                    })

                report_status = agent_result.get(
                    "report_status", "pending"
                )

                tracker_rows.append({
                    "Agent": "Report Agent",
                    "Responsibility": "Evidence consolidation",
                    "Execution Status": report_status.title(),
                })

                st.dataframe(
                    tracker_rows,
                    use_container_width=True,
                    hide_index=True,
                )

                # ------------------------------------------
                # Adaptive investigation journey
                # ------------------------------------------

                st.subheader("Adaptive Investigation Journey")

                execution_trace = agent_result.get("execution_trace", [])
                investigation_decisions = agent_result.get(
                    "investigation_decisions", []
                )

                journey_labels = {
                    "monthly_analysis": "Monthly revenue analysis",
                    "country_analysis": "Country-level investigation",
                    "product_analysis": "Product-level investigation",
                }

                if execution_trace:
                    for index, node_name in enumerate(execution_trace, start=1):
                        label = journey_labels.get(
                            node_name,
                            node_name.replace("_", " ").title(),
                        )
                        st.markdown(f"**{index}. {label}**")
                else:
                    st.info("No adaptive investigation steps were recorded.")

                if investigation_decisions:
                    with st.expander("Why these steps were selected", expanded=True):
                        for decision in investigation_decisions:
                            st.markdown(f"- {decision}")
    

                # ------------------------------------------
                # Supervisor's selected agents
                # ------------------------------------------

                st.subheader("Supervisor's Agent Selection")

                for index, selected in enumerate(
                    agent_result.get("agents_plan", []),
                    start=1,
                ):
                    st.markdown(
                        f"{index}. **{selected['agent'].replace('_', ' ').title()}**"
                        f" — {selected.get('reason', '')}"
                    )

                # ------------------------------------------
                # Individual specialist results
                # ------------------------------------------

                st.divider()
                st.subheader("Specialist Agent Results")

                results_by_agent = {
                    item.get("agent"): item
                    for item in agent_result.get("agent_results", [])
                }

                for specialist in agent_result.get("agent_results", []):

                    agent_name = specialist.get("agent", "unknown")
                    status = specialist.get("status", "unknown")

                    with st.expander(
                        f"{agent_name.replace('_', ' ').title()} — "
                        f"{status.upper()}",
                        expanded=True,
                    ):

                        if status == "failed":
                            st.error(
                                specialist.get(
                                    "error",
                                    "The specialist could not complete its task.",
                                )
                            )
                            continue

                        if status == "partial":
                            st.warning(
                                "The specialist completed only part of its analysis."
                            )

                        # Data Analyst
                        if agent_name == "data_analyst":

                            query_result = specialist.get("result", {})

                            st.caption(
                                "SQL generation source: "
                                f"{query_result.get('source', 'Unknown')}"
                            )

                            sql = query_result.get("sql")

                            if sql:
                                st.markdown("**Generated SQL**")
                                st.code(sql, language="sql")

                            query_data = query_result.get("data")

                            st.markdown("**Query Results**")

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

                        # Investigator
                        elif agent_name == "investigator":

                            investigation_results = specialist.get(
                                "results", {}
                            )

                            revenue = investigation_results.get(
                                "revenue_investigation"
                            )

                            if revenue:
                                st.markdown("**Revenue Investigation**")
                                st.write(
                                    revenue.get(
                                        "summary",
                                        "No investigation summary available.",
                                    )
                                )

                                col1, col2, col3 = st.columns(3)

                                col1.metric(
                                    "Previous Revenue",
                                    f"{revenue.get('previous_revenue', 0):,.2f}",
                                )

                                col2.metric(
                                    "Current Revenue",
                                    f"{revenue.get('current_revenue', 0):,.2f}",
                                )

                                change_pct = revenue.get("change_pct")

                                col3.metric(
                                    "Revenue Change",
                                    (
                                        f"{change_pct:+.1f}%"
                                        if change_pct is not None
                                        else "N/A"
                                    ),
                                )

                                st.markdown("**Key Findings**")

                                for finding in revenue.get("findings", []):
                                    st.markdown(f"- {finding}")

                                country_data = revenue.get("country_drivers")
                                product_data = revenue.get("product_drivers")

                                left, right = st.columns(2)

                                with left:
                                    st.markdown("**Country Revenue Drivers**")
                                    if (
                                        country_data is not None
                                        and not country_data.empty
                                    ):
                                        st.dataframe(
                                            country_data,
                                            use_container_width=True,
                                            hide_index=True,
                                        )
                                    else:
                                        st.info("No country comparison available.")

                                with right:
                                    st.markdown("**Product Revenue Drivers**")
                                    if (
                                        product_data is not None
                                        and not product_data.empty
                                    ):
                                        st.dataframe(
                                            product_data,
                                            use_container_width=True,
                                            hide_index=True,
                                        )
                                    else:
                                        st.info("No product comparison available.")

                                st.markdown("**Suggested Follow-Up Checks**")

                                for recommendation in revenue.get(
                                    "recommendations", []
                                ):
                                    st.markdown(f"- {recommendation}")

                            anomalies = investigation_results.get(
                                "anomalies", []
                            )

                            st.markdown("**Potential Revenue Anomalies**")

                            if anomalies:
                                import pandas as pd

                                st.dataframe(
                                    pd.DataFrame(anomalies),
                                    use_container_width=True,
                                    hide_index=True,
                                )
                            else:
                                st.info("No potential anomalies were flagged.")

                            for error_name, error_message in specialist.get(
                                "errors", {}
                            ).items():
                                st.warning(
                                    f"{error_name}: {error_message}"
                                )

                            st.caption(
                                "Revenue comparisons and anomaly flags "
                                "identify patterns for further investigation; "
                                "they do not prove business causation."
                            )

                        # Knowledge Researcher
                        elif agent_name == "knowledge_researcher":

                            st.markdown("**Retrieved Business Knowledge**")

                            st.write(
                                specialist.get(
                                    "answer",
                                    "No research answer was generated.",
                                )
                            )

                            st.markdown("**Retrieved Document Sources**")

                            for source in specialist.get("sources", []):
                                st.markdown(f"- `{source}`")
                            
                            # RAG Evidence Viewer
                            st.divider()
                            st.markdown("### RAG Evidence Viewer")

                            retrieved_documents = specialist.get(
                                "retrieved_documents", []
                            )

                            if retrieved_documents:
                                st.caption(
                                    f"Retrieved {len(retrieved_documents)} "
                                    "document(s) from the ChromaDB knowledge base."
                                )

                                for index, document in enumerate(
                                    retrieved_documents, start=1
                                ):
                                    source = document.get(
                                        "source", "Unknown source"
                                    )
                                    category = document.get(
                                        "category", "General"
                                    )
                                    distance = document.get("distance")

                                    with st.expander(
                                        f"Document {index}: {source}",
                                        expanded=index == 1,
                                    ):
                                        st.write(
                                            f"**Category:** {category}"
                                        )

                                        if isinstance(
                                            distance, (int, float)
                                        ):
                                            st.caption(
                                                f"ChromaDB distance: "
                                                f"{distance:.4f} "
                                                "(lower generally indicates a closer match)"
                                            )

                                        st.markdown("**Retrieved Content**")
                                        st.write(
                                            document.get(
                                                "document",
                                                "No document content available.",
                                            )
                                        )
                            else:
                                st.info(
                                    "No retrieved document evidence is available."
                                )


                # ------------------------------------------
                # Final consolidated report
                # ------------------------------------------

                st.divider()
                st.subheader("Consolidated Business Intelligence Report")

                final_report = agent_result.get(
                    "final_report",
                    "No final report was generated.",
                )

                if agent_result.get("report_status") == "completed":
                    st.success("Final report generated successfully.")
                else:
                    st.error("Report generation was unsuccessful.")

                with st.expander(
                    "View Complete Investigation Report",
                    expanded=True,
                ):
                    st.markdown(final_report)

                    st.download_button(
                        label="Download Report (.md)",
                        data=final_report,
                        file_name="multi_agent_bi_report.md",
                        mime="text/markdown",
                        key="download_multi_agent_report",
                    )

            except Exception as error:
                st.error(
                    "The multi-agent analysis could not be completed."
                )
                st.exception(error)
except Exception as error:
    st.error("The dashboard could not load its data.")
    st.exception(error)