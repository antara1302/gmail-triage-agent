from core.gmail_client import get_latest_email
from core.triage_agent import run_triage


email = get_latest_email()

if not email:
    print("No emails found.")
    exit()


print("\n" + "=" * 60)
print("GMAIL EMAIL")
print("=" * 60)

print("FROM:", email["sender"])
print("SUBJECT:", email["subject"])

print("\nBODY:")
print(email["body"])


print("\n" + "=" * 60)
print("RUNNING GMAIL TRIAGE")
print("=" * 60)


result = run_triage(
    message_text=email["body"],
    original_subject=email["subject"],
    agent_name="Gmail Triage Agent"
)


print("\nURGENCY:", result["urgency"])
print("INTENT:", result["intent"])
print("CONFIDENCE:", result["confidence"])

print("\nGENERATED SUBJECT:")
print(result["draft_response"]["subject"])

print("\nGENERATED RESPONSE:")
print(result["draft_response"]["body"])