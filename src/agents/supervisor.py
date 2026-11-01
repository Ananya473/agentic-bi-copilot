
import json
import os

from dotenv import load_dotenv
from google import genai


load_dotenv()

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

AGENT_DESCRIPTIONS = {
    "data_analyst": (
        "Handles SQL queries, revenue metrics, KPIs, "
        "customer analytics, products and business data."
    ),
    "investigator": (
        "Investigates revenue changes, compares periods, "
        "identifies country and product drivers, and detects anomalies."
    ),
    "knowledge_researcher": (
        "Retrieves information from business documents, "
        "including return policies, promotions, inventory "
        "and customer behaviour."
    ),
}


def rule_based_routing(question: str) -> list[dict]:
    """Select specialist agents using deterministic rules."""

    q = question.lower()

    agents = []

    investigation_words = [
        "why", "decline", "declined", "decrease",
        "decreased", "drop", "dropped", "fall",
        "fell", "increase", "increased", "growth",
        "anomaly", "anomalies", "outlier", "spike",
        "investigate", "compare", "root cause",
    ]

    knowledge_words = [
        "policy", "policies", "return", "refund",
        "promotion", "promotional", "campaign",
        "inventory", "stock", "out of stock",
        "customer behaviour", "customer behavior",
        "purchasing behaviour", "purchasing behavior",
    ]

    if any(word in q for word in investigation_words):
        agents.append({
            "agent": "investigator",
            "reason": "The question requires investigation or anomaly analysis."
        })

    if any(word in q for word in knowledge_words):
        agents.append({
            "agent": "knowledge_researcher",
            "reason": "The question requires business document research."
        })

    # Use SQL for metrics, data questions, and combined investigations.
    if (
        not agents
        or any(word in q for word in [
            "revenue", "sales", "orders", "customers",
            "products", "country", "countries", "kpi",
            "units", "data", "sql",
        ])
    ):
        agents.append({
            "agent": "data_analyst",
            "reason": "The question requires structured business data analysis."
        })

    return agents


def plan_agents(question: str) -> dict:
    """
    Supervisor:
    Select the specialist agents required to answer a question.
    """

    if not question or not question.strip():
        raise ValueError("Please enter a business question.")

    question = question.strip()

    descriptions = "\n".join(
        f"- {name}: {description}"
        for name, description in AGENT_DESCRIPTIONS.items()
    )

    prompt = f"""
You are the Supervisor of a multi-agent retail
business intelligence system.

Select the minimum number of specialist agents
needed to answer the user's question.

Available agents:
{descriptions}

Rules:
- Select only the listed agent names.
- Use multiple agents when the question requires
  different kinds of analysis.
- Use data_analyst for structured business data.
- Use investigator for revenue changes, comparisons,
  root-cause investigation and anomalies.
- Use knowledge_researcher for business policies,
  promotions, inventory and customer knowledge.
- Do not invent results.
- Do not execute agents.
- Return valid JSON only in this format:

{{
    "agents": [
        {{
            "agent": "data_analyst",
            "reason": "Reason for selecting this agent"
        }}
    ]
}}

User question:
{question}
"""

    try:
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("Gemini API key unavailable.")

        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
        )

        raw = (response.text or "").strip()

        if raw.startswith("```"):
            lines = raw.splitlines()
            lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            raw = "\n".join(lines).strip()

        start = raw.find("{")
        end = raw.rfind("}")

        if start == -1 or end <= start:
            raise ValueError("Invalid supervisor response.")

        payload = json.loads(raw[start:end + 1])
        proposed_agents = payload.get("agents")

        if not isinstance(proposed_agents, list):
            raise ValueError("Invalid agent list.")

        validated = []
        seen = set()

        for item in proposed_agents:
            if not isinstance(item, dict):
                continue

            name = item.get("agent")

            if name not in AGENT_DESCRIPTIONS:
                continue

            if name in seen:
                continue

            reason = item.get("reason", "")

            if not isinstance(reason, str):
                reason = ""

            validated.append({
                "agent": name,
                "reason": reason[:300],
            })

            seen.add(name)

        if not validated:
            raise ValueError("No valid agents selected.")

        return {
            "source": "Gemini AI",
            "agents": validated,
        }

    except Exception:
        return {
            "source": "Rule-based fallback",
            "agents": rule_based_routing(question),
        }
