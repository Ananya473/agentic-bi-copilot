# Agentic AI Business Intelligence Copilot

An AI-assisted business intelligence dashboard that combines retail sales analytics, interactive visualizations, natural-language-to-SQL generation, and read-only database querying.

## Overview

Business teams need to answer questions about revenue, product performance, customer behavior, and sales trends without manually writing SQL for every analysis.

This project combines a Streamlit dashboard with Google Gemini-powered SQL generation and a SQLite database to make retail sales data easier to explore. Users can ask business questions in natural language, inspect the generated SQL, and view the results through the application.

## Features

- **KPI dashboard:** Track total revenue, order count, units sold, and unique customers.
- **Revenue trends:** Explore monthly revenue patterns.
- **Product analytics:** Identify products by sales volume and revenue.
- **Geographic analysis:** Compare revenue and orders across countries.
- **Customer analytics:** Examine customer-level purchasing activity.
- **Returns and cancellations:** Analyze negative-quantity transactions and cancellation indicators.
- **Natural-language-to-SQL:** Convert supported business questions into SQL using Google Gemini.
- **SQL visibility:** Inspect the generated query and its results.
- **Rule-based fallback:** Support common analytical questions when Gemini is unavailable.
- **Read-only query execution:** Restrict database access to analytical queries.
- **Automated tests:** Validate analytics, SQL generation, and question handling.

## Dataset

This project uses the **UCI Online Retail dataset**, containing transactions from a UK-based online retailer between December 2010 and December 2011.

The dataset includes product descriptions, invoice identifiers, quantities, unit prices, customer identifiers, transaction dates, and countries.

The project imports the source data into SQLite and creates a sales table for positive-quantity sales analysis while retaining the original transaction records for returns and cancellation analysis.

**Data limitations:**
- The source dataset includes returns and cancelled invoices.
- Some transactions do not have customer identifiers.
- The current category field is `Uncategorized` because the source dataset does not provide product categories.
- Revenue figures reflect the dataset's transaction values; they should not be interpreted as audited financial results.

## Technology Stack

- **Python** — application logic and analytics
- **Streamlit** — interactive dashboard
- **Pandas** — data processing and query results
- **SQLite** — retail data storage and SQL execution
- **Google Gemini API** — natural-language SQL generation
- **Pytest** — automated testing

## Project Structure

```text
agentic-bi-copilot/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── data/
│   ├── retail_sales.db
│   └── extracted/
├── src/
│   ├── analytics.py
│   ├── import_online_retail.py
│   ├── insights.py
│   ├── query_engine.py
│   ├── question_service.py
│   └── text_to_sql.py
└── tests/
    ├── test_insights.py
    └── test_text_to_sql.py
```

*The structure above describes the main project files. Your local folders may contain additional files.*

## Getting Started

### 1. Clone the repository

Replace the placeholder with your GitHub repository URL.

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd agentic-bi-copilot
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Prepare the dataset

Download the UCI Online Retail dataset and place the source file at the path expected by `src/import_online_retail.py`.

Run the import script:

```powershell
python -m src.import_online_retail
```

This creates or refreshes `data/retail_sales.db`.

If you distribute a prebuilt database, ensure its provenance, size, and licensing are appropriate for your repository. Do not assume the database is present in a fresh clone.

### 5. Configure Gemini

Create a `.env` file in the project root:

```text
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-3.8-flash
```

Use a model available to your Google AI account. Keep the `.env` file private and never commit API credentials.

The application includes a rule-based fallback for supported questions when Gemini is unavailable.

### 6. Launch the dashboard

```powershell
python -m streamlit run app.py
```

Open the local URL displayed in the terminal.

## Example Business Questions

Try supported questions such as:

- Show revenue by country.
- Show monthly revenue.
- Show the top 10 products by revenue.
- Who are the top 10 customers by revenue?
- What is our total revenue?
- Summarize returns and cancellations.

Supported questions depend on the natural-language SQL logic and the available database columns.

## Testing

Run the test suite from the project root:

```powershell
python -m pytest -v
```

The current verified test run completed with **8 passing tests**.

## Security Considerations

- Never commit API keys or other credentials.
- Keep SQL execution read-only and restrict access to approved tables.
- Validate AI-generated SQL independently of the prompt.
- Treat model-generated queries as untrusted input.
- Avoid exposing sensitive customer-level information in public deployments.

## Limitations and Future Improvements

- The category field currently contains only `Uncategorized`, limiting meaningful category comparisons.
- Rule-based fallback supports a limited set of question patterns.
- Gemini-generated SQL may require additional validation and testing for unfamiliar questions.
- The current application demonstrates AI-assisted analytics; a more advanced agentic workflow could add multi-step investigation, insight evaluation, and evidence-backed recommendations.
- Future improvements include richer business explanations, query evaluation, anomaly investigation, and deployment.

## Author

Developed as a portfolio project demonstrating Python, SQL, data analysis, dashboard development, and AI-assisted business intelligence.
