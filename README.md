# Agentic AI Business Intelligence Copilot

An intelligent multi-agent Business Intelligence system that combines **Agentic AI, Retrieval-Augmented Generation (RAG), Text-to-SQL, and data analytics** to investigate retail business questions and generate evidence-backed reports.

## 1. Project Overview

Traditional Business Intelligence systems often require users to understand SQL, navigate dashboards, and manually investigate business trends.

The Agentic AI Business Intelligence Copilot simplifies this process by allowing users to ask questions in natural language.

Instead of relying on a single AI model, the system uses a supervisor-driven multi-agent architecture. A Supervisor Agent understands the user's question, selects the appropriate specialist agents, and coordinates their execution through LangGraph.

For revenue investigation, the system uses an **adaptive workflow** that determines which analysis steps are necessary based on the results of previous steps.

The system combines structured retail data stored in SQLite with unstructured business documents retrieved through a RAG pipeline.

## 2. Key Features

- **Multi-Agent Architecture:** Specialized agents for data analysis, revenue investigation, and business knowledge retrieval.
- **Supervisor Agent:** Understands incoming questions and selects the appropriate agents.
- **LangGraph Orchestration:** Coordinates agent execution, maintains workflow state, and manages conditional workflow paths.
- **Adaptive Investigation:** Dynamically triggers country-level and product-level investigations based on revenue analysis.
- **Retrieval-Augmented Generation (RAG):** Retrieves relevant business documents using ChromaDB and Gemini embeddings.
- **Natural Language to SQL:** Converts supported business questions into SQL queries with a rule-based fallback.
- **Revenue Investigation:** Compares revenue across periods and identifies country- and product-level contributors.
- **Anomaly Detection:** Identifies unusual daily revenue patterns using rolling median and Median Absolute Deviation (MAD).
- **Evidence-Based Reporting:** Consolidates analytical findings, retrieved document excerpts, and follow-up recommendations.
- **Interactive Streamlit Dashboard:** Displays business analytics, agent execution status, investigation decisions, and reports.
- **Supervisor Evaluation:** Includes a manually labelled evaluation dataset to assess agent selection performance.

## 3. Multi-Agent Architecture

The project follows a supervisor-driven architecture using LangGraph.

### Specialist Agents

| Agent | Responsibility |
|---|---|
| Supervisor Agent | Understands the question and selects the appropriate workflow or specialist agents. |
| Data Analyst Agent | Handles SQL queries, KPIs, revenue, product, and customer analytics. |
| Investigator Agent | Investigates revenue changes and identifies country- and product-level contributors. |
| Knowledge Researcher Agent | Retrieves relevant business documents using RAG. |
| Report Agent | Consolidates agent outputs into an evidence-backed report. |

### Adaptive Investigation Workflow

The adaptive workflow investigates revenue changes in stages instead of executing every analysis for every question.

**Workflow steps:**

1. **Monthly Analysis:** Compares the requested month's revenue with the previous month.
2. **Anomaly Detection:** Identifies unusual daily revenue patterns.
3. **Revenue Decision:** Determines whether revenue declined.
4. **Country Investigation:** If revenue declined, compares country-level revenue.
5. **Country Decision:** Checks whether any country experienced a decline.
6. **Product Investigation:** If a declining country is identified, performs product-level analysis.
7. **Reporting:** Consolidates findings, evidence, and recommendations.
8. **Review:** Completes the workflow.

If revenue did not decline, unnecessary country- and product-level investigations are skipped.

### Adaptive Workflow Diagram

```text
                 USER QUESTION
                       |
                       v
                SUPERVISOR AGENT
                       |
                       v
                 MONTHLY ANALYSIS
                       |
              +--------+--------+
              |                 |
              v                 v
        ANOMALY DETECTION   REVENUE DECLINED?
                              /       \
                            No         Yes
                            |           |
                            |           v
                            |    COUNTRY ANALYSIS
                            |           |
                            |    DECLINING COUNTRY?
                            |       /       \
                            |
