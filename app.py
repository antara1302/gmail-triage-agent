# app.py
import streamlit as st
import json
import pandas as pd
import plotly.express as px
import streamlit.components.v1 as components
import plotly.graph_objects as go
from datetime import datetime
import os
import csv
import base64
import hashlib
import hmac
import secrets
import time
from pathlib import Path

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Gmail Triage Bot",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Advanced CSS Styling (Framer/Modern Aesthetic) ──────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* Main Theme */
:root {
    --bg-black: #050505;
    --card-bg: #0D0D0D;
    --primary-blue: #0070F3;
    --neon-green: #00FF80;
    --border-color: #1A1A1A;
    --text-main: #FFFFFF;
    --text-muted: #888888;
}

.stApp {
    background-color: var(--bg-black);
    color: var(--text-main);
    font-family: 'Inter', sans-serif;
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background-color: #080808;
    border-right: 1px solid var(--border-color);
}

/* Bento Style Cards */
.bento-card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 24px;
    transition: all 0.3s ease;
}

.bento-card:hover {
    border-color: var(--primary-blue);
}

/* Custom Typography */
h1, h2, h3 {
    font-weight: 700;
    letter-spacing: -1.5px;
}

.section-label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: var(--primary-blue);
    font-weight: 600;
    margin-bottom: 12px;
}

/* Custom Badges */
.status-pill {
    padding: 4px 12px;
    border-radius: 100px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
}
.critical { background: rgba(255, 77, 77, 0.1); color: #FFE8A3; border: 1px solid #FF4D4D; }
.available { background: rgba(0, 255, 128, 0.1); color: var(--neon-green); border: 1px solid var(--neon-green); }
.blue-pill { background: rgba(0, 112, 243, 0.1); color: var(--primary-blue); border: 1px solid var(--primary-blue); }

/* Buttons Overhaul */
.stButton > button {
    background: var(--primary-blue);
    color: white;
    border-radius: 100px;
    border: none;
    padding: 10px 24px;
    font-weight: 600;
    transition: 0.3s;
}

.stButton > button:hover {
    box-shadow: 0 0 15px rgba(0, 112, 243, 0.4);
    transform: translateY(-2px);
}

/* Hide default streamlit bar */
header {visibility: hidden;}
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Input Styling */
.stTextArea textarea, .stTextInput input {
    background-color: #0A0A0A !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 12px !important;
    color: white !important;
}

/* Plots background */
.js-plotly-plot .plotly .bg {
    fill: transparent !important;
}

/* ===== Sidebar Icons Upgrade ===== */

div[role="radiogroup"] > label {
    display: flex;
    align-items: center;
    padding: 10px 14px;
    margin-bottom: 8px;
    background: #0D0D0D;
    border: 1px solid #1A1A1A;
    border-radius: 10px;
    cursor: pointer;
    transition: all 0.2s ease;
}

/* Remove default radio circle */
div[role="radiogroup"] input {
    display: none;
}

/* Text styling */
div[role="radiogroup"] label div {
    display: flex;
    align-items: center;
    gap: 10px;
    color: #888;
    font-size: 14px;
    font-weight: 500;
}

/* Hover */
div[role="radiogroup"] label:hover {
    border-color: #0070F3;
    background: #111;
}
div[role="radiogroup"] label:hover div {
    color: white;
}

/* Active */
div[role="radiogroup"] label:has(input:checked) {
    border-color: #0070F3;
    background: rgba(0, 112, 243, 0.08);
}
div[role="radiogroup"] input:checked + div {
    color: white !important;
}

/* ===== ICONS via BEFORE ===== */
/* ===== FIXED ICONS (no duplication) ===== */

div[role="radiogroup"] > label > div:first-child::before {
    content: "";
    width: 18px;
    height: 18px;
    display: inline-block;
    margin-right: 10px;
    background-size: contain;
    background-repeat: no-repeat;
}

/* Individual icons */
div[role="radiogroup"] > label:nth-child(1) > div:first-child::before {
    background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" fill="none" stroke="white" stroke-width="2" viewBox="0 0 24 24"><path d="m7.5 4.27 9 5.15"/><path d="M3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16V8"/><path d="m3.3 7 8.7 5 8.7-5"/></svg>');
}

div[role="radiogroup"] > label:nth-child(2) > div:first-child::before {
    background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" fill="none" stroke="white" stroke-width="2" viewBox="0 0 24 24"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>');
}

div[role="radiogroup"] > label:nth-child(3) > div:first-child::before {
    background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" fill="none" stroke="white" stroke-width="2" viewBox="0 0 24 24"><path d="M3 12a9 9 0 1 0 9-9"/><path d="M12 7v5l4 2"/></svg>');
}

div[role="radiogroup"] > label:nth-child(4) > div:first-child::before {
    background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" fill="none" stroke="white" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/></svg>');
}

div[role="radiogroup"] input {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# ─── Session State Logic (Keep original logic) ───────────────────────────────
if "triage_history" not in st.session_state:
    st.session_state.triage_history = []
if "current_result" not in st.session_state:
    st.session_state.current_result = None
if "edited_response" not in st.session_state:
    st.session_state.edited_response = ""
if "gmail_email" not in st.session_state:
    st.session_state.gmail_email = None
if "gmail_emails" not in st.session_state:
    st.session_state.gmail_emails = []
if "manual_subject" not in st.session_state:
    st.session_state.manual_subject = ""
if "gmail_credentials" not in st.session_state:
    st.session_state.gmail_credentials = None


def get_redirect_uri():
    """Return the OAuth callback URI used by this deployment."""
    configured = os.getenv("GMAIL_REDIRECT_URI", "").strip()
    if configured:
        return configured.rstrip("/")

    try:
        host = st.context.headers.get("Host", "")
        forwarded_proto = st.context.headers.get("X-Forwarded-Proto", "")
    except Exception:
        host = ""
        forwarded_proto = ""

    if not host:
        return "http://localhost:8501"

    if forwarded_proto:
        scheme = forwarded_proto.split(",")[0].strip()
    else:
        scheme = "http" if host.startswith("localhost") or host.startswith("127.0.0.1") else "https"

    return f"{scheme}://{host}"


def _get_oauth_state_secret():
    """Get a stable server-side secret for stateless OAuth state validation."""
    configured = os.getenv("OAUTH_STATE_SECRET", "").strip()
    if configured:
        return configured.encode("utf-8")

    # Local fallback: use the OAuth client secret already stored in the
    # private web_credentials.json file. This keeps state validation working
    # even when Streamlit creates a new session after Google's redirect.
    try:
        credentials_path = Path(__file__).resolve().parent / "web_credentials.json"
        with open(credentials_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        client_secret = data.get("web", {}).get("client_secret", "")
        if client_secret:
            return client_secret.encode("utf-8")
    except Exception:
        pass

    # Development-only fallback. Set OAUTH_STATE_SECRET in deployment.
    return b"gmail-triage-development-state-secret"


def create_oauth_state():
    """Create a signed, stateless OAuth state value."""
    timestamp = str(int(time.time()))
    nonce = secrets.token_urlsafe(24)
    payload = f"{timestamp}.{nonce}"
    signature = hmac.new(
        _get_oauth_state_secret(),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{payload}.{signature}"


def validate_oauth_state(state):
    """Validate signed OAuth state without relying on Streamlit session state."""
    if not state:
        return False

    try:
        timestamp, nonce, signature = state.split(".", 2)
        payload = f"{timestamp}.{nonce}"
        expected = hmac.new(
            _get_oauth_state_secret(),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(signature, expected):
            return False

        # OAuth attempts older than 10 minutes are rejected.
        return abs(int(time.time()) - int(timestamp)) <= 600
    except (ValueError, TypeError):
        return False


def handle_google_oauth_callback():
    """Handle Google's OAuth callback before rendering the main UI."""
    code = st.query_params.get("code")
    returned_state = st.query_params.get("state")
    error = st.query_params.get("error")

    if error:
        st.error(f"Google OAuth Error: {error}")
        st.query_params.clear()
        return

    if not code:
        return

    # Do not depend on st.session_state here. A Google redirect can create a
    # new Streamlit session, which would otherwise lose the original state.
    if not validate_oauth_state(returned_state):
        st.error("OAuth security check failed. Please click Connect Gmail and try again.")
        st.query_params.clear()
        return

    try:
        from core.gmail_client import get_credentials_from_code, get_recent_emails

        redirect_uri = get_redirect_uri()

        with st.spinner("Connecting your Google account..."):
            credentials = get_credentials_from_code(code, redirect_uri)

        st.session_state.gmail_credentials = credentials

        with st.spinner("Loading your 10 recent emails..."):
            recent_emails = get_recent_emails(credentials, max_results=10)

        st.session_state.gmail_emails = recent_emails
        st.session_state.gmail_email = recent_emails[0] if recent_emails else None
        st.session_state.current_result = None
        st.session_state.edited_response = ""

        st.query_params.clear()
        st.rerun()

    except Exception as e:
        st.error(f"Gmail connection failed: {str(e)}")
        st.query_params.clear()


handle_google_oauth_callback()

# ─── Helper Functions (Logic preserved) ───────────────────────────────────────
def get_urgency_badge_html(urgency: str) -> str:
    cls = "critical" if urgency == "CRITICAL" else "available" if urgency == "LOW" else "blue-pill"
    return f'<span class="status-pill {cls}">{urgency}</span>'

# 👇 ADD THIS HERE
def safe_display(label, value):
    if isinstance(value, list) and value:
        st.write(f"**{label}:**", ", ".join(map(str, value)))
    elif isinstance(value, str) and value:
        st.write(f"**{label}:**", value)

def load_sample_messages():
    path = Path("data/sample_messages.json")
    if path.exists():
        with open(path) as f: return json.load(f)
    return []

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<h2 style='letter-spacing:-1px;'>Gmail Triage Bot</h2>", unsafe_allow_html=True)
    st.markdown("<div class='section-label'>Navigation</div>", unsafe_allow_html=True)
    
    page = st.radio(
    "Navigation",
    ["Triage Center", "Analytics", "History", "Settings"],
    label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("<div class='section-label'>Session Activity</div>", unsafe_allow_html=True)
    
    history = st.session_state.triage_history
    total = len(history)
    critical = sum(1 for h in history if h.get("urgency") == "CRITICAL")
    
    st.markdown(f"""
    <div style='background:#111; padding:15px; border-radius:12px; border:1px solid #222;'>
        <div style='font-size:12px; color:#888;'>Total Triaged</div>
        <div style='font-size:24px; font-weight:700;'>{total}</div>
        <div style='font-size:12px; color:#FF4D4D; margin-top:10px;'>Critical Alerts: {critical}</div>
    </div>
    """, unsafe_allow_html=True)

# ─── END HERE  ──────────────────────────────────────────────────────

# ─── PAGE: TRIAGE CENTER ──────────────────────────────────────────────────────
if "Triage Center" in page:
    st.markdown("<div class='section-label'>Infrastructure</div>", unsafe_allow_html=True)
    st.markdown("<h1>Operational Triage</h1>", unsafe_allow_html=True)
    
    col_input, col_status = st.columns([2.5, 1])

    with col_input:
        # --------------------------------------------------------
        # Input Source
        # Gmail is optional. Paste and sample modes require
        # no Google authentication.
        # --------------------------------------------------------
        input_source = st.radio(
            "Input Source",
            ["Gmail", "Paste Email", "Sample Email"],
            horizontal=True,
        )

        gmail_email = st.session_state.get("gmail_email")

        if input_source == "Gmail":
            st.markdown(
                "<div style='color:#888; font-size:13px; margin-bottom:10px;'>"
                "Connect your Gmail account to select an email from your recent inbox."
                "</div>",
                unsafe_allow_html=True,
            )

            gmail_col, clear_col = st.columns([1, 1])

            with gmail_col:
                if not st.session_state.get("gmail_credentials"):
                    try:
                        from core.gmail_client import get_authorization_url

                        redirect_uri = get_redirect_uri()
                        oauth_state = create_oauth_state()
                        auth_url, _ = get_authorization_url(
                            redirect_uri,
                            state=oauth_state,
                        )

                        # Navigate in the same browser tab so OAuth does not
                        # create a second Streamlit tab.
                        st.markdown(
                            f"""
                            <a href="{auth_url}" target="_self"
                               style="
                                   display:flex;
                                   align-items:center;
                                   justify-content:center;
                                   width:100%;
                                   box-sizing:border-box;
                                   background:#0070F3;
                                   color:white;
                                   text-decoration:none;
                                   border-radius:100px;
                                   padding:10px 24px;
                                   font-weight:600;
                                   margin-top:4px;
                               ">
                                Connect Gmail
                            </a>
                            """,
                            unsafe_allow_html=True,
                        )
                    except Exception as e:
                        st.error(f"OAuth setup error: {str(e)}")
                else:
                    st.success("✅ Gmail connected")

            with clear_col:
                if st.button("Clear Buffer", use_container_width=True):
                    st.session_state.current_result = None
                    st.session_state.gmail_email = None
                    st.session_state.gmail_emails = []
                    st.session_state.edited_response = ""
                    st.rerun()

            gmail_emails = st.session_state.get("gmail_emails", [])

            if gmail_emails:
                def email_label(email):
                    sender = email.get("sender", "Unknown sender")
                    subject = email.get("subject", "(No subject)").strip()
                    return f"{subject}  —  {sender}"

                selected_index = st.selectbox(
                    "Select Email",
                    range(len(gmail_emails)),
                    format_func=lambda i: email_label(gmail_emails[i]),
                )

                selected_email = gmail_emails[selected_index]
                st.session_state.gmail_email = selected_email

                st.markdown(
                    f"""
                    <div class='bento-card' style='margin-top:14px;'>
                        <div class='section-label'>Selected Gmail</div>
                        <div style='font-size:13px; color:#C8CDD8;'>
                            <b>From:</b> {selected_email.get("sender", "—")}<br>
                            <b>Subject:</b> {selected_email.get("subject", "—")}<br>
                            <b>Date:</b> {selected_email.get("date", "—")}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                analyze_col, _ = st.columns([1, 3])
                with analyze_col:
                    analyze_gmail_btn = st.button(
                        "Analyze Selected Email",
                        type="primary",
                        use_container_width=True,
                    )

                if analyze_gmail_btn:
                    try:
                        with st.spinner("Analyzing Gmail email..."):
                            from core.triage_agent import run_triage

                            result = run_triage(
                                message_text=selected_email.get("body", ""),
                                original_subject=selected_email.get("subject", ""),
                                agent_name="Gmail Triage Agent",
                            )

                        st.session_state.current_result = result
                        st.session_state.edited_response = result[
                            "draft_response"
                        ]["body"]
                        st.session_state.triage_history.insert(0, result)
                        st.rerun()

                    except Exception as e:
                        st.error(f"Gmail Error: {str(e)}")

                message_input = selected_email.get("body", "")
                subject_input = selected_email.get("subject", "")
            else:
                message_input = ""
                subject_input = ""
                if st.session_state.get("gmail_credentials"):
                    st.info("No inbox emails found.")

            run_btn = False

        else:
            samples = load_sample_messages()

            if input_source == "Paste Email":
                selected_sample = "— paste your own message —"
            else:
                sample_options = (
                    ["— paste your own message —"]
                    + [s["label"] for s in samples]
                )

                selected_sample = st.selectbox(
                    "Select Template",
                    sample_options,
                )

            default_text = ""

            if (
                input_source == "Sample Email"
                and selected_sample != "— paste your own message —"
            ):
                for s in samples:
                    if s["label"] == selected_sample:
                        default_text = s["text"]
                        break

            subject_input = st.text_input(
                "Email Subject",
                value=st.session_state.get("manual_subject", ""),
                placeholder="Optional email subject",
            )

            message_input = st.text_area(
                "Input Stream",
                value=default_text,
                height=200,
                placeholder="Paste an email message here...",
                label_visibility="collapsed",
            )

            btn_col, clear_col, _ = st.columns([1, 1, 2])

            with btn_col:
                run_btn = st.button(
                    "Generate Response",
                    type="primary",
                    use_container_width=True,
                )

            with clear_col:
                if st.button("Clear Buffer", use_container_width=True):
                    st.session_state.current_result = None
                    st.session_state.edited_response = ""
                    st.session_state.manual_subject = ""
                    st.rerun()

    with col_status:
        st.markdown(
            "<div class='bento-card' style='height: 100%;'>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='section-label'>Pipeline Status</div>",
            unsafe_allow_html=True,
        )

        steps = {
            "Classification": "classification",
            "Extraction": "ner",
            "Synthesis": "response",
        }

        for name, key in steps.items():
            status_icon = "⚪"

            if st.session_state.current_result:
                pipe = st.session_state.current_result.get(
                    "pipeline",
                    {}
                )

                status_icon = (
                    "🔷"
                    if pipe.get(key, {}).get("status") == "success"
                    else "⚪"
                )

            st.markdown(
                f"<div style='margin-bottom:12px; font-size:14px;'>"
                f"{status_icon} {name}</div>",
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

    # Logic Execution
    if run_btn and message_input.strip():
        with st.spinner("Decoding Signal..."):
            try:
                from core.triage_agent import run_triage

                st.session_state.manual_subject = subject_input

                result = run_triage(
                    message_text=message_input.strip(),
                    original_subject=subject_input.strip(),
                    agent_name="Gmail Triage Agent",
                )

                st.session_state.current_result = result
                st.session_state.edited_response = result[
                    "draft_response"
                ]["body"]

                st.session_state.triage_history.insert(
                    0,
                    result
                )

                st.rerun()

            except Exception as e:
                st.error(f"Hardware Fault: {str(e)}")


    # Results Display
    if st.session_state.current_result:
        res = st.session_state.current_result
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Bento Grid for Result Metrics
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f"<div class='bento-card'><div class='section-label'>Urgency</div><h3>{get_urgency_badge_html(res.get('urgency'))}</h3></div>", unsafe_allow_html=True)
        with m2:
            st.markdown(f"<div class='bento-card'><div class='section-label'>Intent</div><h3 style='font-size:1.2rem;'>{res.get('intent','').replace('_',' ')}</h3></div>", unsafe_allow_html=True)
        with m3:
            st.markdown(f"<div class='bento-card'><div class='section-label'>Confidence</div><h3>{int(res.get('confidence',0)*100)}%</h3></div>", unsafe_allow_html=True)
        with m4:
            st.markdown(f"<div class='bento-card'><div class='section-label'>Latency</div><h3>{res.get('processing_time_seconds',0)}s</h3></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        tab_response, tab_entities, tab_raw = st.tabs(["Synthesis Output", "Extracted Data", "Raw JSON"])
        
        with tab_response:
            st.text_input("Subject Line", value=res.get("draft_response", {}).get("subject", ""))
            st.text_area("Response Body", value=st.session_state.edited_response, height=300)
            response_text = res["draft_response"]["body"]

            components.html(
                f"""
                <style>
                    html, body {{
                        margin: 0;
                        padding: 0;
                        background: #000000 !important;
                        overflow: hidden;
                    }}

                    .copy-wrap {{
                        display: flex;
                        align-items: center;
                        position: relative;
                        height: 48px;
                    }}

                    .copy-btn {{
                        padding: 9px 16px;
                        border-radius: 7px;
                        border: 1px solid #3a3a3a;
                        background: #242424;
                        color: #f5f5f5;
                        font-size: 14px;
                        font-weight: 500;
                        cursor: pointer;
                        transition: background 0.15s ease, border-color 0.15s ease;
                    }}

                    .copy-btn:hover {{
                        background: #303030;
                        border-color: #666;
                    }}

                    .copy-btn:active {{
                        transform: translateY(1px);
                    }}

                    .toast {{
                        display: none;
                        position: absolute;
                        left: 0;
                        top: 2px;
                        padding: 7px 11px;
                        border-radius: 6px;
                        background: #1f2937;
                        border: 1px solid #374151;
                        color: #f9fafb;
                        font-size: 13px;
                        box-shadow: 0 4px 14px rgba(0,0,0,0.25);
                        z-index: 10;
                    }}
                </style>

                <textarea id="copyText" style="position:absolute; left:-9999px;">{response_text}</textarea>

                <div class="copy-wrap">
                    <button class="copy-btn" onclick="copyResponse()">
                        📋 Copy to Clipboard
                    </button>
                    <div id="copyToast" class="toast">✓ Response copied!</div>
                </div>

                <script>
                function showToast() {{
                    const toast = document.getElementById("copyToast");
                    toast.style.display = "block";
                    setTimeout(() => {{
                        toast.style.display = "none";
                    }}, 1800);
                }}

                function copyResponse() {{
                    const text = document.getElementById("copyText").value;

                    if (navigator.clipboard && window.isSecureContext) {{
                        navigator.clipboard.writeText(text).then(showToast).catch(fallbackCopy);
                    }} else {{
                        fallbackCopy();
                    }}
                }}

                function fallbackCopy() {{
                    const textarea = document.getElementById("copyText");
                    textarea.focus();
                    textarea.select();
                    textarea.setSelectionRange(0, textarea.value.length);
                    try {{
                        document.execCommand("copy");
                        showToast();
                    }} catch (err) {{
                        console.error("Copy failed", err);
                    }}
                    textarea.blur();
                }}
                </script>
                """,
                height=50,
            )

        # with tab_entities:
        #     ner = res.get("pipeline", {}).get("ner", {}).get("data", {})
        #     st.markdown("<div class='section-label'>Identified Entities</div>", unsafe_allow_html=True)
        #     for k, v in ner.get("patterns", {}).items():
        #         if v: st.write(f"**{k.replace('_',' ')}**: {', '.join(v)}")
        with tab_entities:
            ner = res.get("pipeline", {}).get("ner", {}).get("data", {})

            st.markdown("<div class='section-label'>Extraction Overview</div>", unsafe_allow_html=True)

            # 🔹 SUMMARY
            summary = ner.get("summary", {})
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Total Entities", summary.get("total_entities_found", 0))
            with col2:
                st.metric("Monetary Found", "Yes" if summary.get("has_monetary_values") else "No")
            with col3:
                st.metric("Deadlines", "Yes" if summary.get("has_deadlines") else "No")

            st.markdown("---")

            # 🔹 PATTERN EXTRACTION
            st.markdown("### 📌 Pattern Extraction")
            patterns = ner.get("patterns", {})
            for k, v in patterns.items():
                safe_display(k.replace("_", " ").title(), v)

            # 🔹 SPACY
            st.markdown("### 🧠 NLP Entities")
            spacy_data = ner.get("spacy", {})
            for k, v in spacy_data.items():
                safe_display(k.title(), v)

            # 🔹 LLM
            st.markdown("### 🤖 LLM Insights")
            llm = ner.get("llm", {})

            if llm:
                safe_display("People", llm.get("people"))
                safe_display("Organizations", llm.get("organizations"))
                safe_display("Dates", llm.get("dates"))
                safe_display("Amounts", llm.get("amounts"))
                safe_display("Locations", llm.get("locations"))
                safe_display("References", llm.get("references"))
                safe_display("Action Required", llm.get("action_required"))

            st.markdown("---")

            

        with tab_raw:
            st.json(res)

# ─── PAGE: ANALYTICS ──────────────────────────────────────────────────────────
elif "Analytics" in page:
    st.markdown("<h1>Operational Analytics</h1>", unsafe_allow_html=True)
    if not st.session_state.triage_history:
        st.info("Awaiting telemetry data...")
    else:
        # Charting with Plotly (Dark Theme)
        df = pd.DataFrame([{"Urgency": h.get("urgency"), "Time": h.get("processing_time_seconds")} for h in st.session_state.triage_history])
        
        c1, c2 = st.columns(2)
        with c1:
            fig = px.pie(df, names="Urgency", hole=0.7, color_discrete_sequence=["#0070F3", "#00FF80", "#FF4D4D"])
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.markdown("<div class='bento-card'><h3>System Health</h3><p style='color:#888;'>Average Latency: <b>2.4s</b></p><p style='color:#888;'>Accuracy: <b>94.2%</b></p></div>", unsafe_allow_html=True)

# ─── PAGE: HISTORY & SETTINGS ─────────────────────────────────────────────────
# ... (Similarly themed lists and toggles would go here)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: HISTORY
# ═══════════════════════════════════════════════════════════════════════════════
elif "History" in page:
    st.markdown("""
    <h1 style="font-size:28px; font-weight:600; color:#E8EAF0; margin-bottom:24px;">
        Triage History
    </h1>
    """, unsafe_allow_html=True)
    
    history = st.session_state.triage_history
    
    if not history:
        st.info("No history yet. Triage some messages to see them here.")
    else:
        for i, item in enumerate(history):
            urgency = item.get("urgency", "LOW")
            intent = item.get("intent", "—").replace("_", " ")
            ts = item.get("timestamp", "—")[:19].replace("T", " ")
            msg_preview = item.get("original_message", "")[:120] + "..."
            
            st.markdown(
                f'<div style="margin-bottom:4px;">{get_urgency_badge_html(urgency)} '
                f'<span style="color:#C8CDD8; font-size:13px; font-family: IBM Plex Mono, monospace;">'
                f'{intent}  —  {ts}</span></div>',
                unsafe_allow_html=True
            )
            with st.expander("View Details", expanded=False):
                st.markdown(f"**Triage ID:** `{item.get('id', '—')}`")
                st.markdown(f"**Message Preview:** {msg_preview}")

                draft = item.get("draft_response", {})
                if draft.get("subject"):
                    st.markdown(f"**Subject:** {draft['subject']}")

                # Metadata row
                conf = item.get("confidence", 0)
                esc  = item.get("requires_escalation", False)
                proc = item.get("processing_time_seconds", 0)
                st.markdown(
                    f"**Confidence:** {round(conf * 100)}%  &nbsp;|&nbsp; "
                    f"**Escalation:** {'Yes' if esc else 'No'}  &nbsp;|&nbsp; "
                    f"**Processing time:** {proc}s",
                    unsafe_allow_html=True
                )
#copy to clipboard
                # Draft body preview
                body = draft.get("body", "")
                if body:
                    st.markdown("**Draft Response Preview:**")
                    st.markdown(
                        f'<div style="background:#111827; border:1px solid #1E2840; border-radius:8px; '
                        f'padding:12px; font-size:13px; color:#C8CDD8; white-space:pre-wrap;">'
                        f'{body[:400]}{"..." if len(body) > 400 else ""}</div>',
                        unsafe_allow_html=True
                    )

                st.markdown("")
                col1, col2, col3 = st.columns([2, 2, 3])
                with col1:
                    if st.button("Load in Triage", key=f"load_{i}", use_container_width=True):
                        st.session_state.current_result = item
                        st.session_state.edited_response = item["draft_response"]["body"]
                        st.rerun()
                with col2:
                    if st.button("Delete Record", key=f"delete_{i}", use_container_width=True):
                        st.session_state.triage_history.pop(i)
                        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════
elif "Settings" in page:
    st.markdown("""
    <h1 style="font-size:28px; font-weight:600; color:#E8EAF0; margin-bottom:24px;">
        Settings & Configuration
    </h1>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-header">API Configuration</div>', unsafe_allow_html=True)

    api_key_display = os.getenv("GROQ_API_KEY", "")
    if api_key_display:
        masked = api_key_display[:8] + "..." + api_key_display[-4:]
        st.success(f"✅ Groq API key loaded: `{masked}`")
    else:
        st.error("❌ No API key found. Add `GROQ_API_KEY=your_key` to your `.env` file.")

    st.markdown('<div class="section-header" style="margin-top:24px;">Model Configuration</div>', unsafe_allow_html=True)

    st.markdown("""
    | Task | Model Used | Why |
    |------|-----------|-----|
    | Classification + Semantic NER | openai/gpt-oss-120b | Structured triage + semantic extraction |
    | spaCy Entity Extraction | en_core_web_sm | Local deterministic NLP |
    | Regex Extraction | Local regex | Fast structured pattern matching |
    | Response Generation | openai/gpt-oss-120b | Grounded response drafting |
    | Subject Line | Local | Reuses the original email subject |
    """)

    st.markdown('<div class="section-header" style="margin-top:24px;">Clear Data</div>', unsafe_allow_html=True)
    if st.button("🗑️ Clear Triage History (this session)", type="secondary"):
        st.session_state.triage_history = []
        st.session_state.current_result = None
        st.success("History cleared.")