"""Server-side Gmail Web OAuth client for gmail-triage-bot."""

import base64
from email.utils import parseaddr
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build


BASE_DIR = Path(__file__).resolve().parent.parent
WEB_CREDENTIALS_FILE = BASE_DIR / "web_credentials.json"
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def create_oauth_flow(redirect_uri: str) -> Flow:
    """Create the Web OAuth flow with PKCE explicitly disabled."""
    if not WEB_CREDENTIALS_FILE.exists():
        raise FileNotFoundError(
            f"Missing {WEB_CREDENTIALS_FILE.name} in the project root."
        )

    return Flow.from_client_secrets_file(
        str(WEB_CREDENTIALS_FILE),
        scopes=SCOPES,
        redirect_uri=redirect_uri,
        autogenerate_code_verifier=False,
    )


def get_authorization_url(redirect_uri: str, state: str | None = None):
    """Build Google's account-selection/consent URL."""
    flow = create_oauth_flow(redirect_uri)

    return flow.authorization_url(
        state=state,
        access_type="offline",
        include_granted_scopes="true",
        prompt="select_account consent",
    )


def get_credentials_from_code(
    code: str,
    redirect_uri: str,
    state: str | None = None,
) -> Credentials:
    """Exchange Google's authorization code for user credentials."""
    flow = create_oauth_flow(redirect_uri)

    # PKCE is disabled on both authorization and callback flows, so Google
    # will not require a code_verifier here.
    flow.fetch_token(code=code)
    return flow.credentials


def build_gmail_service(credentials: Credentials):
    return build("gmail", "v1", credentials=credentials, cache_discovery=False)


def extract_body(payload: dict) -> str:
    if not payload:
        return ""

    body_data = payload.get("body", {}).get("data")
    mime_type = payload.get("mimeType", "")

    if body_data and mime_type == "text/plain":
        try:
            return base64.urlsafe_b64decode(body_data).decode(
                "utf-8", errors="replace"
            )
        except Exception:
            return ""

    parts = payload.get("parts", []) or []

    # Prefer plain text.
    for part in parts:
        if part.get("mimeType") == "text/plain":
            text = extract_body(part)
            if text:
                return text

    # Then recursively inspect multipart sections.
    for part in parts:
        text = extract_body(part)
        if text:
            return text

    if body_data:
        try:
            return base64.urlsafe_b64decode(body_data).decode(
                "utf-8", errors="replace"
            )
        except Exception:
            pass

    return ""


def parse_email(message: dict) -> dict:
    payload = message.get("payload", {})
    headers = payload.get("headers", []) or []

    header_map = {
        h.get("name", "").lower(): h.get("value", "")
        for h in headers
    }

    raw_sender = header_map.get("from", "Unknown sender")
    sender_name, sender_email = parseaddr(raw_sender)

    if sender_name and sender_email:
        sender = f"{sender_name} <{sender_email}>"
    else:
        sender = raw_sender

    return {
        "id": message.get("id", ""),
        "thread_id": message.get("threadId", ""),
        "sender": sender,
        "sender_email": sender_email,
        "subject": header_map.get("subject", "(No subject)"),
        "date": header_map.get("date", ""),
        "body": extract_body(payload),
    }


def get_recent_emails(credentials: Credentials, max_results: int = 10):
    """Fetch up to max_results recent inbox emails for this Google user."""
    service = build_gmail_service(credentials)

    response = (
        service.users()
        .messages()
        .list(
            userId="me",
            maxResults=max_results,
            q="in:inbox",
        )
        .execute()
    )

    emails = []
    for ref in response.get("messages", []):
        message = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=ref["id"],
                format="full",
            )
            .execute()
        )
        emails.append(parse_email(message))

    return emails


def get_latest_email(credentials: Credentials):
    emails = get_recent_emails(credentials, max_results=1)
    return emails[0] if emails else None
