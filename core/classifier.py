import os
import json
import re

from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

URGENCY_LEVELS = {
    "CRITICAL": {"color": "#FF3B3B", "icon": "🔴", "sla": "1 hour"},
    "HIGH": {"color": "#FF8C00", "icon": "🟠", "sla": "4 hours"},
    "MEDIUM": {"color": "#FFD700", "icon": "🟡", "sla": "24 hours"},
    "LOW": {"color": "#00C851", "icon": "🟢", "sla": "72 hours"},
}


INTENT_TYPES = [
    "MEETING",
    "RECRUITMENT",
    "ACCOUNT_SUPPORT",
    "CUSTOMER_SUPPORT",
    "FINANCE",
    "COMPLAINT",
    "REQUEST",
    "INFORMATION",
    "FOLLOW_UP",
    "SOCIAL",
    "GENERAL_INQUIRY",
]


def analyze_message(text: str) -> dict:

    prompt = f"""
Classify this email.

EMAIL:
{text}

Return ONLY one valid JSON object with exactly this structure:

{{
  "classification": {{
    "urgency": "MEDIUM",
    "intent": "GENERAL_INQUIRY",
    "confidence": 0.94,
    "reasoning": "Brief reason based only on the email.",
    "key_concern": "Main issue raised by the sender.",
    "sentiment": "NEUTRAL",
    "requires_escalation": false
  }},
  "entities": {{
    "people": [],
    "organizations": [],
    "dates": [],
    "amounts": [],
    "locations": [],
    "references": [],
    "action_required": ""
  }}
}}

Rules:

- Return valid JSON only.
- No markdown.
- No explanation outside the JSON.
- Do not invent information.
- Use [] when no entities are found.
- Use an empty string when action_required cannot be determined.
- urgency must be CRITICAL, HIGH, MEDIUM, or LOW.
- intent must be one of:
  MEETING,
  RECRUITMENT,
  ACCOUNT_SUPPORT,
  CUSTOMER_SUPPORT,
  FINANCE,
  COMPLAINT,
  REQUEST,
  INFORMATION,
  FOLLOW_UP,
  SOCIAL,
  GENERAL_INQUIRY.
- Do not classify an email as FINANCE unless it is actually related to financial matters.
- Do not assume the sender is a customer, client, employee, or business contact.
- Do not invent company policies, deadlines, contact information, or required actions.
- confidence must be between 0 and 1.
- sentiment must be POSITIVE, NEUTRAL, or NEGATIVE.
- requires_escalation must be true or false.
- action_required must be under 15 words.
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        max_tokens=1000,
        reasoning_effort="low",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an intelligent email triage system. "
                    "Extract only information explicitly supported by "
                    "the email and classify it accurately. "
                    "Return exactly one valid JSON object."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    raw = response.choices[0].message.content

    if not raw:
        raise ValueError("Groq returned an empty analysis response")

    raw = raw.strip()

    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        raw = raw.strip()

    try:
        return json.loads(raw)

    except json.JSONDecodeError as e:
        print("INVALID ANALYSIS RESPONSE:")
        print(repr(raw))
        raise ValueError(
            f"Analysis model returned invalid JSON: {e}"
        )