import re


# ============================================================
# spaCy
# ============================================================

try:
    import spacy

    nlp = spacy.load("en_core_web_sm")
    SPACY_AVAILABLE = True

except Exception:
    SPACY_AVAILABLE = False


def extract_with_spacy(text: str) -> dict:
    """
    Extract common named entities using spaCy.

    No LLM call is made here.
    """

    if not SPACY_AVAILABLE:
        return {
            "persons": [],
            "organizations": [],
            "dates": [],
            "money": [],
            "locations": [],
        }

    doc = nlp(text)

    entities = {
        "persons": [],
        "organizations": [],
        "dates": [],
        "money": [],
        "locations": [],
    }

    for ent in doc.ents:

        if ent.label_ == "PERSON":
            entities["persons"].append(ent.text)

        elif ent.label_ == "ORG":
            entities["organizations"].append(ent.text)

        elif ent.label_ in ("DATE", "TIME"):
            entities["dates"].append(ent.text)

        elif ent.label_ == "MONEY":
            entities["money"].append(ent.text)

        elif ent.label_ in ("GPE", "LOC"):
            entities["locations"].append(ent.text)

    return entities


# ============================================================
# Regex / Pattern Extraction
# ============================================================

def extract_patterns(text: str) -> dict:
    """
    Extract useful structured information using regex.

    This is intentionally domain-neutral so the triage bot
    can process different types of Gmail messages.
    """

    return {

        # ----------------------------------------------------
        # Invoice / reference IDs
        # ----------------------------------------------------

        "invoice_ids": re.findall(
            r"\b(?:INV|INVOICE|inv)[-#]?\s*\d{4,10}\b",
            text,
            re.IGNORECASE,
        ),

        # ----------------------------------------------------
        # Account numbers
        # ----------------------------------------------------

        "account_numbers": re.findall(
            r"\b(?:ACC|ACCT|Account)[-#]?\s*\d{6,12}\b",
            text,
            re.IGNORECASE,
        ),

        # ----------------------------------------------------
        # Transaction / reference IDs
        # ----------------------------------------------------

        "transaction_ids": re.findall(
            r"\b(?:TXN|TRX|REF|TRANS)[-#]?\s*[A-Z0-9]{6,15}\b",
            text,
            re.IGNORECASE,
        ),

        # ----------------------------------------------------
        # General reference IDs
        # ----------------------------------------------------

        "reference_ids": re.findall(
            r"\b(?:ID|CASE|TICKET|REQUEST|ORDER)[-#]?\s*[A-Z0-9]{4,20}\b",
            text,
            re.IGNORECASE,
        ),

        # ----------------------------------------------------
        # Monetary amounts
        # ----------------------------------------------------

        "amounts": re.findall(
            r"(?:USD|EUR|GBP|INR|₹|\$|€|£)\s*[\d,]+(?:\.\d{2})?"
            r"|\b\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*"
            r"(?:USD|EUR|GBP|INR)\b",
            text,
            re.IGNORECASE,
        ),

        # ----------------------------------------------------
        # Email addresses
        # ----------------------------------------------------

        "email_addresses": re.findall(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
            text,
        ),

        # ----------------------------------------------------
        # Phone numbers
        # ----------------------------------------------------

        "phone_numbers": re.findall(
            r"\b(?:\+\d{1,3}[-.\s]?)?"
            r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
            text,
        ),
    }


# ============================================================
# Combined Entity Extraction
# ============================================================

def extract_all_entities(text: str) -> dict:
    """
    Combine deterministic NLP extraction.

    NOTE:
    This function intentionally does NOT call an LLM.

    Semantic classification and semantic entity extraction
    are handled together by classifier.analyze_message().
    """

    spacy_entities = extract_with_spacy(text)
    pattern_entities = extract_patterns(text)

    total_entities = (
        len(spacy_entities.get("persons", []))
        + len(spacy_entities.get("organizations", []))
        + len(spacy_entities.get("dates", []))
        + len(spacy_entities.get("money", []))
        + len(spacy_entities.get("locations", []))
        + len(pattern_entities.get("invoice_ids", []))
        + len(pattern_entities.get("account_numbers", []))
        + len(pattern_entities.get("transaction_ids", []))
        + len(pattern_entities.get("reference_ids", []))
        + len(pattern_entities.get("amounts", []))
        + len(pattern_entities.get("email_addresses", []))
        + len(pattern_entities.get("phone_numbers", []))
    )

    return {
        "spacy": spacy_entities,

        "patterns": pattern_entities,

        # Kept for compatibility with the existing UI/pipeline.
        # Semantic LLM entities are added later by triage_agent.py.
        "llm": {},

        "summary": {
            "total_entities_found": total_entities,

            "has_monetary_values": bool(
                spacy_entities.get("money")
                or pattern_entities.get("amounts")
            ),

            "has_deadlines": bool(
                spacy_entities.get("dates")
            ),

            "action_required": "",
        },
    }