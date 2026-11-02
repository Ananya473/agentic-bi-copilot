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
                            |      No        Yes
                            |      |          |
                            |      |          v
                            |      |    PRODUCT ANALYSIS
                            |      |          |
                            +------+----------+
                                   |
                                   v
                              REPORT AGENT
                                   |
                                   v
                                REVIEWER
                                   |
                                   v
                             FINAL BI REPORT
```

Daily anomaly detection is performed during the monthly-analysis stage. The regular specialist-execution workflow is also available for other types of business questions.

## 4. Adaptive Revenue Investigation

The adaptive workflow uses analysis results to determine the next step.

- If monthly revenue did not decline, deeper country- and product-level investigation is skipped.
- If monthly revenue declined, country-level analysis is triggered.
- If country analysis identifies a declining country, product-level investigation is triggered.
- Daily anomaly detection is performed during monthly analysis.

### Example: December 2011 Revenue Decline

A verified workflow run using the question:

`Why did revenue decrease in December 2011?`

Produced the following results:

| Metric | Result |
|---|---:|
| November 2011 Revenue | 1,509,496.33 |
| December 2011 Revenue | 638,792.68 |
| Revenue Change | -57.68% |
| Daily Records Analyzed | 305 |
| Potential Anomalies Detected | 9 |

The workflow proceeded through monthly analysis, country investigation, and product investigation.

The UK recorded the largest country-level revenue decline, while RABBIT NIGHT LIGHT recorded the largest product-level decline.

These findings represent observed revenue changes, not verified business causes. The system provides follow-up checks to help investigate possible explanations.

## 5. Anomaly Detection

The system identifies unusual daily revenue patterns using a rolling statistical baseline.

### Methodology

- **Rolling Median:** Estimates expected revenue using previous observations.
- **Median Absolute Deviation (MAD):** Measures how far a revenue observation deviates from the rolling median.
- **Anomaly Threshold:** Uses a configurable MAD-based threshold and minimum percentage-change condition.
- **Anomaly Classification:** Identifies potential high-revenue and low-revenue days.

The anomaly output includes:

- Date
- Actual revenue
- Expected revenue
- Revenue deviation
- Percentage deviation
- Anomaly type

The current implementation analyzes transaction-active dates returned by the analytics query rather than every calendar date.

Anomaly detection identifies unusual patterns that require further investigation; it does not independently establish their causes.

## 6. Retrieval-Augmented Generation (RAG)

The system uses RAG to answer questions that require business knowledge beyond the structured retail database.

### RAG Pipeline

1. Business documents are loaded from the knowledge-base directory.
2. Gemini embeddings convert document content into vector representations.
3. ChromaDB stores document embeddings and associated metadata.
4. Relevant documents are retrieved through semantic similarity search.
5. The Knowledge Researcher generates answers grounded in the retrieved context.

### Knowledge Base Documents

The demonstration knowledge base includes:

- Return Policy
- Promotional Campaigns
- Inventory Management
- Customer Behaviour

**Note:** These are synthetic demonstration documents created for the project. They should not be interpreted as verified policies of the retailer in the dataset.

## 7. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application development |
| LangGraph | Multi-agent workflow orchestration |
| Google Gemini API | Agent planning, embeddings, and language generation |
| ChromaDB | Vector database for semantic retrieval |
| Streamlit | Interactive application interface |
| SQLite | Structured retail data storage |
| Pandas | Data processing and analysis |
| Plotly | Interactive data visualizations |
| SQL | Business queries and analytical operations |
| Pytest | Automated testing |

## 8. Dataset

The project uses the **UCI Online Retail Dataset**, containing transactions from a UK-based online retailer between December 2010 and December 2011.

The dataset includes:

- Invoice numbers
- Product descriptions
- Quantities
- Unit prices
- Customer identifiers
- Invoice dates
- Countries

The dataset is imported into SQLite for structured analysis.

The analytical pipeline distinguishes positive-quantity sales from returns and cancellations.

## 9. Project Structure

```text
agentic-bi-copilot/
│
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
│
├── data/
│   └── Online Retail.xlsx
│
├── chroma_db/
│   └── Generated vector database
│
├── src/
│   ├── agents/
│   │   ├── supervisor.py
│   │   ├── data_analyst.py
│   │   ├── investigator_agent.py
│   │   ├── knowledge_researcher.py
│   │   └── report_agent.py
│   │
│   ├── graph/
│   │   ├── state.py
│   │   ├── nodes.py
│   │   └── workflow.py
│   │
│   ├── knowledge_base/
│   │   ├── vector_store.py
│   │   └── documents/
│   │
│   ├── evaluation/
│   │   └── supervisor_evaluation.py
│   │
│   ├── analytics.py
│   ├── anomaly_detection.py
│   ├── investigator.py
│   ├── reporting.py
│   ├── question_service.py
│   ├── query_engine.py
│   └── text_to_sql.py
│
└── tests/
    └── Automated test modules
```

*Note: This represents the main project structure. Generated databases, local datasets, and other files may be excluded from Git.*

## 10. Installation and Setup

### Prerequisites

- Python 3.11 or later, compatible with project dependencies
- Git
- Google Gemini API key

### Step 1: Clone the Repository

```bash
git clone https://github.com/Ananya473/agentic-bi-copilot.git
cd agentic-bi-copilot
```

### Step 2: Create a Virtual Environment

For Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies

```powershell
python -m pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create a `.env` file in the project root.

```text
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
```

The project uses Google Gemini for supervisor planning, natural-language processing, and knowledge generation.

Model availability and request limits depend on your Google AI account. Rule-based fallback mechanisms help maintain workflow execution when Gemini is unavailable.

### Step 5: Prepare the Dataset

Download the UCI Online Retail dataset and place the Excel file at the location expected by the project's import script.

Run:

```powershell
python -m src.import_online_retail
```

### Step 6: Launch the Application

```powershell
streamlit run app.py
```

Open the local URL displayed in the terminal.

## 11. Example Business Questions

### Data Analyst

- What is the total revenue?
- Which five products generate the highest revenue?
- Which countries have the highest sales?

### Investigator

- Why did revenue change between two months?
- Which countries contributed most to the revenue decline?
- Are there unusual spikes in daily revenue?

### Knowledge Researcher

- Explain the return policy.
- How do promotional campaigns affect customer behaviour?
- How does inventory management handle out-of-stock products?

### Adaptive Multi-Agent Analysis

- Why did revenue decrease in December 2011?
- Which countries and products contributed most to the decline?
- Did revenue decline in March 2011, and is deeper investigation required?

The Supervisor selects agents or the adaptive investigation path based on the question and available routing logic.

## 12. Evaluation and Testing

The project includes automated tests for:

- Analytics
- SQL processing
- Anomaly detection
- Investigation logic
- Agent execution
- Report generation

**Previously verified test result:**

- 56 tests passed.
- 2 deprecation warnings.

The Supervisor Agent also includes a manually labelled evaluation dataset of 10 business questions.

Evaluation metrics include:

- Exact-match routing accuracy
- Precision
- Recall
- F1-score

The evaluation results depend on the selected routing implementation. Rule-based fallback results should not be presented as Gemini model evaluation results.

The adaptive workflow was also manually tested using increasing- and declining-revenue scenarios.

## 13. Limitations

- Gemini API requests are subject to model availability and account-specific quotas.
- The Supervisor uses rule-based routing when Gemini is unavailable.
- Knowledge Researcher response generation requires Gemini, although document retrieval can operate independently.
- Knowledge-base documents are synthetic demonstration data.
- Rule-based routing supports a limited range of question patterns.
- The dataset does not provide meaningful product categories, limiting category-level analysis.
- Daily anomaly detection uses transaction-active dates rather than a fully continuous calendar series.
- Anomaly flags and revenue comparisons identify patterns and associations, not proven business causes.
- The project is a demonstration system and is not intended to replace a production enterprise BI platform.

## 14. Future Scope

- Improve supervisor routing using larger evaluation datasets.
- Add specialist agents for forecasting and customer segmentation.
- Improve agent coordination and recovery from individual agent failures.
- Expand the knowledge base with verified business documents.
- Add advanced business recommendations and decision-support capabilities.
- Improve anomaly detection with calendar-complete time series and additional statistical methods.
- Deploy the application with production-grade monitoring and authentication.

## 15. Author

Developed as an academic and portfolio project demonstrating **Agentic AI, adaptive multi-agent systems, Retrieval-Augmented Generation, Python, SQL, and Business Intelligence**.

**GitHub Repository:** [Agentic AI Business Intelligence Copilot](https://github.com/Ananya473/agentic-bi-copilot)
