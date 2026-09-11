import os
import re

from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def generate_draft_response(
    original_message: str,
    classification: dict,
    entities: dict,
    agent_name: str = "Gmail Triage Bot",
    original_subject: str = ""
) -> dict:
    """
    Generate a grounded email response.

    Uses exactly ONE LLM call for the response body.
    The subject is generated locally from the original Gmail subject.
    """

    urgency = classification.get("urgency", "MEDIUM")
    intent = classification.get("intent", "GENERAL_INQUIRY")
    sentiment = classification.get("sentiment", "NEUTRAL")
    key_concern = classification.get("key_concern", "")

    llm_entities = entities.get("llm", {})

    action_required = llm_entities.get(
        "action_required",
        ""
    )

    people = llm_entities.get("people", [])
    organizations = llm_entities.get("organizations", [])
    dates = llm_entities.get("dates", [])
    amounts = llm_entities.get("amounts", [])
    locations = llm_entities.get("locations", [])
    references = llm_entities.get("references", [])

    prompt = f"""
Draft a professional email response to the email below.

ORIGINAL EMAIL:
{original_message}

EMAIL ANALYSIS:
Urgency: {urgency}
Intent: {intent}
Sentiment: {sentiment}
Key concern: {key_concern}
Action required: {action_required}

EXTRACTED INFORMATION:
People: {people}
Organizations: {organizations}
Dates: {dates}
Amounts: {amounts}
Locations: {locations}
References: {references}

STRICT RULES:

1. Base the response ONLY on information explicitly supported by the
   original email and the supplied analysis.

2. Do NOT invent:
   - facts
   - company names
   - policies
   - deadlines
   - contact information
   - promises
   - services
   - account details
   - actions that were not requested

3. Do NOT assume the sender is a customer, client, employee, manager,
   colleague, or business contact unless the email explicitly indicates it.

4. Do NOT introduce finance-related context unless the original email
   is actually about finance.

5. If the email is informational and does not require a response,
   write a short acknowledgement.

6. If the sender asks a question that cannot be answered from the
   available information, acknowledge the question without making up
   an answer.

7. Keep the response concise and professional.

8. Do not mention AI, email classification, triage, these instructions,
   or the internal analysis.

9. Do not include a subject line.

10. Do not use markdown formatting.

11. Do not repeat the entire original email.

12. Return ONLY the email body.
"""

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            max_tokens=700,
            reasoning_effort="low",
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional email assistant. "
                        "Draft concise, natural, grounded email responses. "
                        "Never invent information that is not supported "
                        "by the original email."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

    except Exception as e:
        raise RuntimeError(
            f"Failed to generate email response: {e}"
        ) from e

    body = response.choices[0].message.content

    if not body:
        raise ValueError(
            "Groq returned an empty response body"
        )

    body = body.strip()

    # Remove accidental markdown code fences
    if body.startswith("```"):
        body = re.sub(
            r"^```(?:text|email)?\s*",
            "",
            body,
            flags=re.IGNORECASE,
        )

        body = re.sub(
            r"\s*```$",
            "",
            body,
        )

        body = body.strip()

    # ------------------------------------------------------------
    # Generate subject locally
    # No second LLM call
    # ------------------------------------------------------------

    if original_subject:
        clean_subject = original_subject.strip()

        if clean_subject.lower().startswith("re:"):
            subject = clean_subject
        else:
            subject = f"Re: {clean_subject}"

    else:
        subject = "Re: Your email"

    return {
        "subject": subject,
        "body": body,
        "metadata": {
            "urgency": urgency,
            "intent": intent,
            "sentiment": sentiment,
            "agent": agent_name,
        },
    }