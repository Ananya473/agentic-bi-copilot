# Agentic AI Business Intelligence Copilot

An intelligent, multi-agent Business Intelligence system that combines **Agentic AI, Retrieval-Augmented Generation (RAG), Text-to-SQL, and data analytics** to investigate retail business questions and generate evidence-backed reports.

## 1. Project Overview

Traditional Business Intelligence systems often require users to understand SQL, navigate dashboards, and manually investigate business trends.

The Agentic AI Business Intelligence Copilot simplifies this process by allowing users to ask questions in natural language.

Instead of relying on a single AI model, the system uses a supervisor-driven multi-agent architecture. A Supervisor Agent understands the user's question, selects the appropriate specialist agents, coordinates their execution through LangGraph, and passes their findings to a Report Agent.

The system combines structured retail data stored in SQLite with unstructured business documents retrieved through a RAG pipeline.

## 2. Key Features

- **Multi-Agent Architecture:** Uses specialized AI agents for structured data analysis, revenue investigation, and business knowledge retrieval.
- **Supervisor Agent:** Analyzes incoming questions and dynamically selects the appropriate specialist agents.
- **LangGraph Orchestration:** Coordinates agent execution, maintains workflow state, and manages the overall analysis pipeline.
- **Retrieval-Augmented Generation (RAG):** Retrieves relevant business documents using ChromaDB and Gemini embeddings.
- **Natural Language to SQL:** Converts supported business questions into SQL queries with a rule-based fallback.
- **Revenue Investigation:** Compares revenue across periods and identifies country- and product-level contributors.
- **Anomaly Detection:** Identifies unusual revenue patterns using rolling median and Median Absolute Deviation (MAD).
- **Evidence-Based Reporting:** Consolidates specialist findings, retrieved document excerpts, and analytical results into a downloadable report.
- **Interactive Streamlit Dashboard:** Provides visual analytics, agent execution status, and multi-agent analysis results.
- **Supervisor Evaluation:** Includes a manually labelled evaluation dataset to assess agent selection performance.

## 3. Multi-Agent Architecture

The project follows a supervisor-driven architecture.

### Workflow

1. **User Input:** The user submits a business question through the Streamlit interface.
2. **Supervisor Agent:** Analyzes the question and determines which specialist agents are required.
3. **Specialist Execution:** The selected agents perform their assigned tasks.
4. **Report Agent:** Consolidates the outputs into a structured business intelligence report.
5. **Final Output:** The user receives the analysis, findings, evidence, and execution summary.

### Specialist Agents

| Agent | Responsibility |
|---|---|
| Supervisor Agent | Understands the question and selects specialist agents. |
| Data Analyst Agent | Handles SQL queries, KPIs, revenue, products, and customer analytics. |
| Investigator Agent | Investigates revenue changes, identifies contributing countries and products, and detects anomalies. |
| Knowledge Researcher Agent | Retrieves relevant business documents using RAG and generates document-grounded answers. |
| Report Agent | Consolidates agent outputs into an evidence-backed report. |

### Architecture Flow

```text
                 USER QUESTION
                       |
                       v
                SUPERVISOR AGENT
                       |
             AGENT SELECTION
                       |
          +------------+------------+
          |            |            |
          v            v            v
     DATA ANALYST  INVESTIGATOR  KNOWLEDGE
       AGENT          AGENT      RESEARCHER
          |            |            |
          v            v            v
       SQL DATA    INVESTIGATION   RAG / CHROMADB
       ANALYSIS    & ANOMALIES     RETRIEVAL
          |            |            |
          +------------+------------+
                       |
                       v
                  REPORT AGENT
                       |
                       v
              FINAL BI REPORT
```

The diagram represents the logical workflow. The supervisor dynamically selects agents based on the incoming question; not every agent runs for every request.

## 4. Retrieval-Augmented Generation (RAG)

The system uses RAG to answer questions that require business knowledge beyond the structured retail database.

### RAG Pipeline

1. Business documents are loaded from the knowledge-base document directory.
2. Gemini embeddings convert document content into vector representations.
3. ChromaDB stores the document embeddings and associated metadata.
4. When a user asks a knowledge-related question, relevant documents are retrieved through semantic similarity search.
5. The Knowledge Researcher uses the retrieved context to generate an answer grounded in the available documents.

### Knowledge Base Documents

The demonstration knowledge base includes:

- Return Policy
- Promotional Campaigns
- Inventory Management
- Customer Behaviour

**Note:** These are synthetic demonstration documents created for the project. They should not be interpreted as verified policies of the retailer in the dataset.

## 5. Technology Stack

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

## 6. Dataset

The project uses the **UCI Online Retail Dataset**, containing transactions from a UK-based online retailer between December 2010 and December 2011.

The dataset includes:

- Invoice numbers
- Product descriptions
- Quantities
- Unit prices
- Customer identifiers
- Invoice dates
- Countries

The source dataset is imported into SQLite for structured analysis.

The analytical pipeline distinguishes positive-quantity sales from returns and cancellations.

## 7. Project Structure

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

Generated databases and local datasets are not necessarily included in the Git repository. Check the repository's `.gitignore` before assuming these files are available after cloning.

## 8. Installation and Setup

### Prerequisites

- Python 3.11 or later, compatible with the project dependencies
- Git
- Google Gemini API key

### Step 1: Clone the Repository

```bash
git clone https://github.com/Ananya473/agentic-bi-copilot.git
cd agentic-bi-copilot
```

### Step 2: Create a Virtual Environment

Windows PowerShell:

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

The project uses Google Gemini for supervisor planning, natural-language processing, and knowledge generation. The configured Gemini model is gemini-3.5-flash-lite. Model availability and request limits depend on your Google AI account. The application includes rule-based fallback mechanisms to maintain workflow execution when Gemini is unavailable.

### Step 5: Prepare the Dataset

Download the UCI Online Retail dataset and place the Excel file at the location expected by the project's import script.

Run the database import process:

```powershell
python -m src.import_online_retail
```

### Step 6: Launch the Application

```powershell
streamlit run app.py
```

Open the local URL displayed in the terminal.

## 9. Example Business Questions

The following questions demonstrate the different capabilities of the system:

**Data Analyst**
- What is the total revenue?
- Which five products generate the highest revenue?
- Which countries have the highest sales?

**Investigator**
- Why did revenue change between two months?
- Which countries contributed most to the revenue decline?
- Are there unusual spikes in daily revenue?

**Knowledge Researcher**
- Explain the return policy.
- How do promotional campaigns affect customer behaviour?
- How does inventory management handle out-of-stock products?

**Multi-Agent Analysis**
- Investigate the revenue decline and check whether promotional campaigns could explain it.

The supervisor selects agents based on the question and the available routing logic.

## 10. Evaluation and Testing

The project includes automated tests for analytics, SQL processing, anomaly detection, investigation logic, agent execution, and report generation.

**Verified test result:**

- 56 tests passed.
- 2 deprecation warnings.

The Supervisor Agent also includes a manually labelled evaluation dataset of 10 business questions.

Its evaluation measures:
- Exact-match routing accuracy
- Precision
- Recall
- F1-score

The evaluation results depend on the selected routing implementation. Rule-based fallback results should not be presented as Gemini model evaluation results.

## 11. Limitations

- Gemini API requests are subject to model availability and account-specific quotas.
- The Supervisor uses rule-based routing when Gemini is unavailable.
- Knowledge Researcher response generation requires Gemini, although document retrieval can operate independently.
- The knowledge-base documents are synthetic demonstration data.
- Rule-based routing supports a limited range of question patterns.
- The dataset does not provide meaningful product categories, so category-level analysis is limited.
- The project is a demonstration system and is not intended to replace a production enterprise BI platform.

## 12. Future Scope

- Improve supervisor routing through larger evaluation datasets.
- Add more specialist agents for forecasting and customer segmentation.
- Improve agent coordination and recovery from individual agent failures.
- Expand the knowledge base with verified business documents.
- Add more advanced business recommendation and decision-support capabilities.
- Deploy the application with production-grade monitoring and authentication.

## 13. Author

Developed as an academic and portfolio project demonstrating Agentic AI, multi-agent systems, Retrieval-Augmented Generation, Python, SQL, and Business Intelligence.
