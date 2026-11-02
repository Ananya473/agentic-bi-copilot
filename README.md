
Agentic AI Business Intelligence Copilot
An intelligent, multi-agent Business Intelligence system that combines Agentic AI, Retrieval-Augmented Generation (RAG), Text-to-SQL, and data analytics to investigate retail business questions and generate evidence-backed reports.

1. Project Overview
Traditional Business Intelligence systems often require users to understand SQL, navigate dashboards, and manually investigate business trends.

The Agentic AI Business Intelligence Copilot simplifies this process by allowing users to ask questions in natural language.

Instead of relying on a single AI model, the system uses a supervisor-driven multi-agent architecture. A Supervisor Agent understands the user's question, selects the appropriate specialist agents, and coordinates execution through LangGraph. For revenue-investigation questions, the workflow can adapt its next steps based on the results of the analysis rather than following a fixed sequence.

The system combines structured retail data stored in SQLite with unstructured business documents retrieved through a RAG pipeline.

2. Key Features
Multi-Agent Architecture: Uses specialized agents for structured data analysis, revenue investigation, and business knowledge retrieval.
Supervisor Agent: Analyzes incoming questions and selects the appropriate specialist agents.
LangGraph Orchestration: Coordinates agent execution, maintains workflow state, and manages conditional workflow paths.
Adaptive Investigation: Checks monthly revenue first and decides whether country-level and product-level investigations are necessary.
Retrieval-Augmented Generation (RAG): Retrieves relevant business documents using ChromaDB and Gemini embeddings.
Natural Language to SQL: Converts supported business questions into SQL queries with a rule-based fallback.
Revenue Investigation: Compares revenue across periods and identifies country- and product-level contributors.
Anomaly Detection: Identifies unusual daily revenue patterns using a rolling median and Median Absolute Deviation (MAD).
Evidence-Based Reporting: Consolidates specialist findings, retrieved document excerpts, analytical results, and follow-up recommendations into a report.
Interactive Streamlit Dashboard: Provides visual analytics, agent execution status, adaptive investigation decisions, and report downloads.
Supervisor Evaluation: Includes a manually labelled evaluation dataset to assess agent selection performance.
3. Multi-Agent Architecture
The project follows a supervisor-driven architecture with two workflow paths:

Regular multi-agent path: The supervisor selects specialist agents, which are executed through the regular specialist executor.
Adaptive investigation path: When a revenue-investigation request is detected, the workflow first analyzes monthly revenue and then conditionally investigates the relevant business dimensions.
Adaptive Investigation Workflow
For a revenue-investigation question, the workflow follows these decisions:

Monthly Analysis: Compares the requested month with the preceding month.
Anomaly Detection: Analyzes daily revenue patterns and flags potential high- or low-revenue anomalies.
Revenue Decision: If revenue did not decline, deeper country- and product-level investigation is skipped.
Country Investigation: If revenue declined, the workflow compares country-level revenue to identify declining contributors.
Country Decision: If a declining country is identified, product-level investigation is triggered.
Product Investigation: Compares product-level revenue to identify products associated with the decline.
Reporting and Review: The Report Agent consolidates findings, evidence, and follow-up checks. A review node completes the workflow.
The adaptive path avoids running every investigation for every question. Its next steps depend on the results produced by earlier analysis nodes.

Adaptive Workflow Diagram
                         USER QUESTION
                               |
                               v
                        SUPERVISOR AGENT
                               |
                    Select investigation path
                               |
                               v
                        MONTHLY ANALYSIS
                         /           \
                        /             \
                       v               v
              DAILY ANOMALY       REVENUE DECLINED?
                DETECTION             /       \
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
The diagram describes the adaptive investigation path. Daily anomaly detection is performed as part of the monthly-analysis stage. The regular specialist-execution path remains available for other question types.

Specialist Agents and Workflow Components
Component	Responsibility
Supervisor Agent	Understands the question and selects the appropriate workflow or specialist agents.
Data Analyst Agent	Handles SQL queries, KPIs, revenue, product, and customer analytics.
Investigator Agent	Investigates revenue changes and identifies country- and product-level contributors.
Knowledge Researcher Agent	Retrieves relevant business documents using RAG and generates document-grounded answers.
Report Agent	Consolidates agent outputs into an evidence-backed report.
Monthly Analysis Node	Compares monthly revenue and initiates daily anomaly detection in adaptive investigations.
Country Analysis Node	Runs when the monthly analysis identifies a revenue decline.
Product Analysis Node	Runs when country-level analysis identifies a declining country.
Reviewer Node	Reviews the completed workflow and records its completion status.
4. Adaptive Revenue Investigation
The adaptive workflow is designed to investigate revenue changes in stages.

Decision Logic
If monthly revenue increased or remained non-declining, the workflow does not continue to country- and product-level investigation.
If monthly revenue declined, country-level analysis is triggered.
If country analysis identifies a declining country, product-level analysis is triggered.
Daily anomaly detection is performed during the monthly-analysis stage, independently of whether deeper investigation is required.
Example: December 2011 Revenue Decline
A verified run using the question Why did revenue decrease in December 2011? produced the following results:

Metric	Result
November 2011 revenue	1,509,496.33
December 2011 revenue	638,792.68
Revenue change	-57.68%
Daily records analyzed	305
Potential daily anomalies flagged	9
The workflow proceeded through monthly analysis, country analysis, and product analysis.

The largest country-level revenue decline was for the UK. The largest product-level decline was for RABBIT NIGHT LIGHT.

These are observed revenue associations, not proof of the underlying business causes. The report presents follow-up checks rather than treating correlations as verified explanations.

5. Anomaly Detection
The system analyzes daily revenue and identifies potential unusual values using a rolling statistical baseline.

Rolling median: Estimates expected revenue from preceding observations.
Median Absolute Deviation (MAD): Measures how far a daily revenue value is from the rolling median in a robust way.
Anomaly threshold: Uses a configurable MAD-based threshold and a minimum percentage-change condition.
Anomaly labels: Flags potential high-revenue and low-revenue days.
The anomaly output includes the date, actual revenue, expected revenue, deviation, percentage deviation, and anomaly type.

The current daily revenue analysis uses transaction-active dates returned by the analytics query. Therefore, the rolling baseline is calculated over those returned observations rather than every calendar date.

An anomaly is a signal for further investigation; it does not by itself establish why the revenue value occurred.

6. Retrieval-Augmented Generation (RAG)
The system uses RAG to answer questions that require business knowledge beyond the structured retail database.

RAG Pipeline
Business documents are loaded from the knowledge-base document directory.
Gemini embeddings convert document content into vector representations.
ChromaDB stores the document embeddings and associated metadata.
When a user asks a knowledge-related question, relevant documents are retrieved through semantic similarity search.
The Knowledge Researcher uses the retrieved context to generate an answer grounded in the available documents.
Knowledge Base Documents
The demonstration knowledge base includes:

Return Policy
Promotional Campaigns
Inventory Management
Customer Behaviour
Note: These are synthetic demonstration documents created for the project. They should not be interpreted as verified policies of the retailer in the dataset.

7. Technology Stack
Technology	Purpose
Python	Core application development
LangGraph	Multi-agent workflow orchestration and adaptive routing
Google Gemini API	Agent planning, embeddings, and language generation
ChromaDB	Vector database for semantic retrieval
Streamlit	Interactive application interface
SQLite	Structured retail data storage
Pandas	Data processing and analysis
Plotly	Interactive data visualizations
SQL	Business queries and analytical operations
Pytest	Automated testing
8. Dataset
The project uses the UCI Online Retail Dataset, containing transactions from a UK-based online retailer between December 2010 and December 2011.

The dataset includes:

Invoice numbers
Product descriptions
Quantities
Unit prices
Customer identifiers
Invoice dates
Countries
The source dataset is imported into SQLite for structured analysis.

The analytical pipeline distinguishes positive-quantity sales from returns and cancellations.

9. Project Structure
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
Generated databases and local datasets are not necessarily included in the Git repository. Check the project's .gitignore before assuming these files are available after cloning.

10. Installation and Setup
Prerequisites
Python 3.11 or later, compatible with the project dependencies
Git
Google Gemini API key
Step 1: Clone the Repository
git clone https://github.com/Ananya473/agentic-bi-copilot.git
cd agentic-bi-copilot
Step 2: Create a Virtual Environment
Windows PowerShell:

python -m venv .venv
.\.venv\Scripts\Activate.ps1
Step 3: Install Dependencies
python -m pip install -r requirements.txt
Step 4: Configure Environment Variables
Create a .env file in the project root.

GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
The project uses Google Gemini for supervisor planning, natural-language processing, and knowledge generation. The configured Gemini model is gemini-3.5-flash-lite. Model availability and request limits depend on your Google AI account. The application includes rule-based fallback mechanisms to maintain workflow execution when Gemini is unavailable.

Step 5: Prepare the Dataset
Download the UCI Online Retail dataset and place the Excel file at the location expected by the project's import script.

Run the database import process:

python -m src.import_online_retail
Step 6: Launch the Application
streamlit run app.py
Open the local URL displayed in the terminal.

11. Example Business Questions
The following questions demonstrate the different capabilities of the system.

Data Analyst

What is the total revenue?
Which five products generate the highest revenue?
Which countries have the highest sales?
Investigator

Why did revenue change between two months?
Which countries contributed most to the revenue decline?
Are there unusual spikes in daily revenue?
Knowledge Researcher

Explain the return policy.
How do promotional campaigns affect customer behaviour?
How does inventory management handle out-of-stock products?
Adaptive Multi-Agent Analysis

Why did revenue decrease in December 2011?
Investigate the revenue decline and identify the countries and products with the largest decreases.
Did revenue decline in March 2011, and should deeper investigation be performed?
The supervisor selects agents or the adaptive investigation path based on the question and available routing logic.

12. Evaluation and Testing
The project includes automated tests for analytics, SQL processing, anomaly detection, investigation logic, agent execution, and report generation.

Previously verified test result:

56 tests passed.
2 deprecation warnings.
The Supervisor Agent also includes a manually labelled evaluation dataset of 10 business questions.

Its evaluation measures:

Exact-match routing accuracy
Precision
Recall
F1-score
The evaluation results depend on the selected routing implementation. Rule-based fallback results should not be presented as Gemini model evaluation results.

The adaptive workflow was also manually exercised with both increasing- and declining-revenue questions. The declining-revenue scenario triggered country- and product-level analysis, while the increasing-revenue scenario skipped those deeper investigation stages.

13. Limitations
Gemini API requests are subject to model availability and account-specific quotas.
The Supervisor uses rule-based routing when Gemini is unavailable.
Knowledge Researcher response generation requires Gemini, although document retrieval can operate independently.
The knowledge-base documents are synthetic demonstration data.
Rule-based routing supports a limited range of question patterns.
The dataset does not provide meaningful product categories, so category-level analysis is limited.
Daily anomaly detection uses transaction-active dates returned by the analytics query, not a fully continuous calendar series.
Anomaly flags and revenue comparisons identify patterns and associations; they do not independently establish business causation.
The project is a demonstration system and is not intended to replace a production enterprise BI platform.
14. Future Scope
Improve supervisor routing through larger evaluation datasets.
Add more specialist agents for forecasting and customer segmentation.
Improve agent coordination and recovery from individual agent failures.
Expand the knowledge base with verified business documents.
Add more advanced business recommendation and decision-support capabilities.
Improve anomaly detection with calendar-complete time series and additional statistical methods.
Deploy the application with production-grade monitoring and authentication.
15. Author
Developed as an academic and portfolio project demonstrating Agentic AI, adaptive multi-agent systems, Retrieval-Augmented Generation, Python, SQL, and Business Intelligence.

