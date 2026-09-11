import time
from datetime import datetime

from core.classifier import analyze_message, URGENCY_LEVELS
from core.ner_extractor import extract_with_spacy, extract_patterns
from core.response_generator import generate_draft_response


def run_triage(
    message_text: str,
    agent_name: str = "Gmail Triage Agent",
    original_subject: str = ""
) -> dict:

    start_time = time.time()

    result = {
        "id": f"TRG-{int(time.time())}",
        "timestamp": datetime.now().isoformat(),
        "original_message": message_text,
        "original_subject": original_subject,
        "status": "processing",
        "pipeline": {}
    }

    # ============================================================
    # STEP 1: Hybrid Entity Extraction
    # spaCy + Regex
    # No LLM call
    # ============================================================

    try:
        spacy_entities = extract_with_spacy(message_text)
        pattern_entities = extract_patterns(message_text)

        result["pipeline"]["ner"] = {
            "status": "success",
            "data": {
                "spacy": spacy_entities,
                "patterns": pattern_entities
            }
        }

    except Exception as e:

        result["pipeline"]["ner"] = {
            "status": "error",
            "error": str(e)
        }

        spacy_entities = {}
        pattern_entities = {}

    # ============================================================
    # STEP 2: Classification + Semantic Entity Extraction
    # LLM CALL #1
    # ============================================================

    try:

        analysis = analyze_message(message_text)

        classification = analysis.get(
            "classification",
            {
                "urgency": "MEDIUM",
                "intent": "GENERAL_INQUIRY",
                "confidence": 0.5,
                "requires_escalation": False
            }
        )

        llm_entities = analysis.get(
            "entities",
            {
                "people": [],
                "organizations": [],
                "dates": [],
                "amounts": [],
                "locations": [],
                "references": [],
                "action_required": ""
            }
        )

        # --------------------------------------------------------
        # Combine deterministic + LLM entity extraction
        # --------------------------------------------------------

        entities = {
            "spacy": spacy_entities,
            "patterns": pattern_entities,
            "llm": llm_entities,

            "summary": {
                "total_entities_found": (
                    len(llm_entities.get("people", []))
                    + len(llm_entities.get("organizations", []))
                    + len(llm_entities.get("dates", []))
                    + len(llm_entities.get("amounts", []))
                    + len(llm_entities.get("locations", []))
                    + len(llm_entities.get("references", []))
                ),

                "has_monetary_values": bool(
                    llm_entities.get("amounts")
                    or pattern_entities.get("amounts")
                    or spacy_entities.get("money")
                ),

                "has_deadlines": bool(
                    llm_entities.get("dates")
                    or spacy_entities.get("dates")
                ),

                "action_required": llm_entities.get(
                    "action_required",
                    ""
                )
            }
        }

        result["pipeline"]["classification"] = {
            "status": "success",
            "data": classification
        }

        result["pipeline"]["ner"]["data"] = entities

    except Exception as e:

        result["pipeline"]["classification"] = {
            "status": "error",
            "error": str(e)
        }

        classification = {
            "urgency": "MEDIUM",
            "intent": "GENERAL_INQUIRY",
            "confidence": 0.5,
            "requires_escalation": False
        }

        entities = {
            "spacy": spacy_entities,
            "patterns": pattern_entities,
            "llm": {},

            "summary": {
                "total_entities_found": 0,
                "has_monetary_values": False,
                "has_deadlines": False,
                "action_required": ""
            }
        }

    # ============================================================
    # STEP 3: Generate Draft Response
    # LLM CALL #2
    # ============================================================

    try:

        draft = generate_draft_response(
            original_message=message_text,
            classification=classification,
            entities=entities,
            agent_name=agent_name,
            original_subject=original_subject
        )

        result["pipeline"]["response"] = {
            "status": "success",
            "data": draft
        }

    except Exception as e:

        result["pipeline"]["response"] = {
            "status": "error",
            "error": str(e)
        }

        draft = {
            "subject": (
                f"Re: {original_subject}"
                if original_subject
                else "Re: Your email"
            ),
            "body": (
                "Thank you for your email. "
                "We will review it and get back to you."
            ),
            "metadata": {}
        }

    # ============================================================
    # FINAL RESULT
    # ============================================================

    elapsed = round(time.time() - start_time, 2)

    result.update({

        "status": "complete",

        "urgency": classification.get(
            "urgency",
            "MEDIUM"
        ),

        "intent": classification.get(
            "intent",
            "GENERAL_INQUIRY"
        ),

        "confidence": classification.get(
            "confidence",
            0.5
        ),

        "urgency_meta": URGENCY_LEVELS.get(
            classification.get(
                "urgency",
                "MEDIUM"
            ),
            {}
        ),

        "entities_summary": entities.get(
            "summary",
            {}
        ),

        "draft_response": draft,

        "processing_time_seconds": elapsed,

        "requires_escalation": classification.get(
            "requires_escalation",
            False
        ),
    })

    return result