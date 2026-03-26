# app.py
import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import csv
from pathlib import Path

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Finance Triage Agent",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS Styling ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

/* Base */
html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}

/* Hide default Streamlit elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Background */
.stApp {
    background-color: #0A0E17;
    color: #E8EAF0;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #0D1220;
    border-right: 1px solid #1E2840;
}

/* Cards */
.metric-card {
    background: linear-gradient(135deg, #111827 0%, #1a2035 100%);
    border: 1px solid #1E2840;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 12px;
}

.urgency-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 20px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    font-weight: 500;
    letter-spacing: 0.5px;
}

.badge-critical { background: rgba(255,59,59,0.15); color: #FF3B3B; border: 1px solid rgba(255,59,59,0.3); }
.badge-high { background: rgba(255,140,0,0.15); color: #FF8C00; border: 1px solid rgba(255,140,0,0.3); }
.badge-medium { background: rgba(255,215,0,0.15); color: #FFD700; border: 1px solid rgba(255,215,0,0.3); }
.badge-low { background: rgba(0,200,81,0.15); color: #00C851; border: 1px solid rgba(0,200,81,0.3); }

.entity-tag {
    display: inline-block;
    background: rgba(66,153,225,0.12);
    color: #63B3ED;
    border: 1px solid rgba(66,153,225,0.25);
    border-radius: 6px;
    padding: 2px 10px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11px;
    margin: 2px;
}

.pipeline-step {
    background: #111827;
    border-left: 3px solid #3B82F6;
    padding: 12px 16px;
    margin: 8px 0;
    border-radius: 0 8px 8px 0;
}

.pipeline-step.success { border-left-color: #10B981; }
.pipeline-step.error { border-left-color: #EF4444; }

.response-box {
    background: #0D1220;
    border: 1px solid #1E2840;
    border-radius: 10px;
    padding: 20px;
    font-family: 'IBM Plex Sans', sans-serif;
    line-height: 1.7;
    color: #C8CDD8;
    white-space: pre-wrap;
}

.section-header {
    font-size: 11px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #4B5675;
    font-weight: 600;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid #1E2840;
}

.stat-number {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 28px;
    font-weight: 500;
    line-height: 1;
}

.info-row {
    display: flex;
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px solid #1A2035;
    font-size: 13px;
}
.info-row:last-child { border-bottom: none; }
.info-label { color: #4B5675; }
.info-value { color: #C8CDD8; font-family: 'IBM Plex Mono', monospace; font-size: 12px; }

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #1D4ED8, #2563EB);
    color: white;
    border: none;
    border-radius: 8px;
    font-family: 'IBM Plex Sans', sans-serif;
    font-weight: 500;
    transition: all 0.2s;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #2563EB, #3B82F6);
    transform: translateY(-1px);
}

/* Text areas */
.stTextArea textarea {
    background: #111827 !important;
    border: 1px solid #1E2840 !important;
    border-radius: 8px !important;
    color: #E8EAF0 !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #0D1220;
    border-radius: 8px;
    padding: 4px;
    border: 1px solid #1E2840;
}
.stTabs [data-baseweb="tab"] {
    color: #4B5675;
    border-radius: 6px;
}
.stTabs [aria-selected="true"] {
    background: #1E2840;
    color: #E8EAF0 !important;
}

/* Expander */
.streamlit-expanderHeader {
    background: #111827 !important;
    border-radius: 8px !important;
}
</style>
""", unsafe_allow_html=True)


# ─── Session State Init ───────────────────────────────────────────────────────
if "triage_history" not in st.session_state:
    st.session_state.triage_history = []
if "current_result" not in st.session_state:
    st.session_state.current_result = None
if "edited_response" not in st.session_state:
    st.session_state.edited_response = ""


# ─── Helper Functions ─────────────────────────────────────────────────────────
def get_urgency_badge_html(urgency: str) -> str:
    icons = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}
    cls = urgency.lower()
    icon = icons.get(urgency, "⚪")
    return f'<span class="urgency-badge badge-{cls}">{icon} {urgency}</span>'


def load_sample_messages():
    path = Path("data/sample_messages.json")
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return []


def save_to_log(result: dict):
    """Append triage result to CSV log."""
    log_path = Path("data/triage_log.csv")
    row = {
        "id": result.get("id"),
        "timestamp": result.get("timestamp"),
        "urgency": result.get("urgency"),
        "intent": result.get("intent"),
        "confidence": result.get("confidence"),
        "processing_time": result.get("processing_time_seconds"),
        "requires_escalation": result.get("requires_escalation"),
        "message_preview": result.get("original_message", "")[:80],
    }
    file_exists = log_path.exists()
    with open(log_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏦 Finance Triage")
    st.markdown('<div class="section-header">Navigation</div>', unsafe_allow_html=True)
    
    page = st.radio(
        "",
        ["🔍 Triage Center", "📊 Analytics", "📋 History", "⚙️ Settings"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown('<div class="section-header">Quick Stats</div>', unsafe_allow_html=True)
    
    history = st.session_state.triage_history
    total = len(history)
    critical = sum(1 for h in history if h.get("urgency") == "CRITICAL")
    escalations = sum(1 for h in history if h.get("requires_escalation"))
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total", total)
        st.metric("Critical", critical)
    with col2:
        st.metric("Escalations", escalations)
        avg_time = round(sum(h.get("processing_time_seconds", 0) for h in history) / max(total, 1), 1)
        st.metric("Avg Time", f"{avg_time}s")
    
    st.markdown("---")
    
    # Agent name config
    agent_name = st.text_input(
        "Agent / Team Name",
        value="Finance Operations Team",
        help="This name appears in generated responses"
    )
    
    # API key check
    api_key = os.getenv("GROQ_API_KEY", "")
    if api_key:
        st.success("✓ API Connected")
    else:
        st.error("✗ No API Key found in .env")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: TRIAGE CENTER
# ═══════════════════════════════════════════════════════════════════════════════
if "Triage Center" in page:
    
    # Header
    st.markdown("""
    <div style="margin-bottom: 24px;">
        <div style="font-size:11px; letter-spacing:3px; color:#4B5675; text-transform:uppercase; margin-bottom:4px;">
            AI-Powered Finance Operations
        </div>
        <h1 style="font-size:28px; font-weight:600; margin:0; color:#E8EAF0;">
            Triage Center
        </h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Input area
    col_left, col_right = st.columns([3, 1])
    
    with col_left:
        st.markdown('<div class="section-header">Incoming Communication</div>', unsafe_allow_html=True)
        
        # Sample message selector
        samples = load_sample_messages()
        sample_options = ["— paste your own message —"] + [s["label"] for s in samples]
        selected_sample = st.selectbox("Load a sample message:", sample_options)
        
        # Pre-fill text area if sample selected
        default_text = ""
        if selected_sample != "— paste your own message —":
            for s in samples:
                if s["label"] == selected_sample:
                    default_text = s["text"]
                    break
        
        message_input = st.text_area(
            "Message Content",
            value=default_text,
            height=180,
            placeholder="Paste or type incoming finance communication here...",
            label_visibility="collapsed"
        )
    
    with col_right:
        st.markdown('<div class="section-header">Pipeline Status</div>', unsafe_allow_html=True)
        
        steps = ["Classification", "NER Extraction", "Response Gen"]
        for step in steps:
            status = "⬜"
            if st.session_state.current_result:
                step_key = step.lower().replace(" ", "_").replace("ner_extraction", "ner").replace("response_gen", "response")
                pipe = st.session_state.current_result.get("pipeline", {})
                if step_key in pipe:
                    status = "✅" if pipe[step_key]["status"] == "success" else "❌"
                else:
                    # Try alternate key mapping
                    key_map = {"Classification": "classification", "NER Extraction": "ner", "Response Gen": "response"}
                    k = key_map.get(step, "")
                    if k in pipe:
                        status = "✅" if pipe[k]["status"] == "success" else "❌"
            st.markdown(f"**{status} {step}**")
        
        if st.session_state.current_result:
            t = st.session_state.current_result.get("processing_time_seconds", 0)
            st.markdown(f"⏱️ **{t}s total**")
    
    # Run button
    run_col, clear_col, _ = st.columns([2, 1, 3])
    
    with run_col:
        run_btn = st.button("▶  Run Triage Pipeline", type="primary", use_container_width=True)
    with clear_col:
        if st.button("✕  Clear", use_container_width=True):
            st.session_state.current_result = None
            st.rerun()
    
    # ── Run Pipeline ──────────────────────────────────────────────────────────
    if run_btn and message_input.strip():
        with st.spinner("Running triage pipeline..."):
            try:
                from core.triage_agent import run_triage
                result = run_triage(message_input.strip(), agent_name=agent_name)
                st.session_state.current_result = result
                st.session_state.edited_response = result["draft_response"]["body"]
                st.session_state.triage_history.insert(0, result)
                save_to_log(result)

                for step, data in result.get("pipeline", {}).items():
                    if data.get("status") == "error":
                        st.error(f"Step '{step}' failed: {data.get('error')}")

                st.rerun()
            except Exception as e:
                st.error(f"Pipeline error: {str(e)}")
                st.exception(e)

    elif run_btn:
        st.warning("Please enter a message to triage.")
    
    # ── Results Display ───────────────────────────────────────────────────────
    if st.session_state.current_result:
        result = st.session_state.current_result
        
        st.markdown("---")
        
        # Top metrics row
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            urgency = result.get("urgency", "MEDIUM")
            sla = result.get("urgency_meta", {}).get("sla", "—")
            st.markdown(f"""
            <div class="metric-card">
                <div class="section-header">Urgency Level</div>
                {get_urgency_badge_html(urgency)}
                <div style="font-size:12px; color:#4B5675; margin-top:8px;">SLA: {sla}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with c2:
            intent = result.get("intent", "—").replace("_", " ")
            st.markdown(f"""
            <div class="metric-card">
                <div class="section-header">Intent Type</div>
                <div style="font-size:15px; font-weight:500; color:#E8EAF0;">{intent}</div>
                <div style="font-size:12px; color:#4B5675; margin-top:8px;">
                    Confidence: {round(result.get('confidence', 0) * 100)}%
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with c3:
            esc = result.get("requires_escalation", False)
            esc_color = "#FF3B3B" if esc else "#00C851"
            esc_text = "YES — Escalate" if esc else "NO — Standard"
            st.markdown(f"""
            <div class="metric-card">
                <div class="section-header">Escalation</div>
                <div style="font-size:15px; font-weight:500; color:{esc_color};">{esc_text}</div>
                <div style="font-size:12px; color:#4B5675; margin-top:8px;">
                    Triage ID: {result.get('id', '—')}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with c4:
            ent_count = result.get("entities_summary", {}).get("total_entities_found", 0)
            proc_time = result.get("processing_time_seconds", 0)
            st.markdown(f"""
            <div class="metric-card">
                <div class="section-header">Processing</div>
                <div class="stat-number" style="color:#3B82F6;">{proc_time}s</div>
                <div style="font-size:12px; color:#4B5675; margin-top:8px;">
                    {ent_count} entities extracted
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Tabs for detailed results
        tab1, tab2, tab3, tab4 = st.tabs([
            "📝 Draft Response", "🔎 Entities", "📊 Classification", "🔩 Raw Pipeline"
        ])
        
        # TAB 1: Draft Response
        with tab1:
            draft = result.get("draft_response", {})
            
            st.markdown('<div class="section-header">Generated Subject Line</div>', unsafe_allow_html=True)
            subject_edit = st.text_input("", value=draft.get("subject", ""), label_visibility="collapsed")
            
            st.markdown('<div class="section-header" style="margin-top:16px;">Draft Response Body</div>', unsafe_allow_html=True)
            edited = st.text_area(
                "",
                value=st.session_state.edited_response,
                height=300,
                label_visibility="collapsed",
                key="response_editor"
            )
            st.session_state.edited_response = edited
            
            btn_col1, btn_col2, btn_col3 = st.columns(3)
            with btn_col1:
                if st.button("📋 Copy Response", use_container_width=True):
                    st.toast("Response copied to clipboard!", icon="✅")
            with btn_col2:
                if st.button("✅ Mark as Sent", use_container_width=True):
                    st.toast("Marked as sent!", icon="✅")
            with btn_col3:
                if st.button("🔄 Regenerate", use_container_width=True):
                    with st.spinner("Regenerating..."):
                        from core.response_generator import generate_draft_response
                        new_draft = generate_draft_response(
                            result["original_message"],
                            result["pipeline"]["classification"]["data"],
                            result["pipeline"]["ner"]["data"],
                            agent_name
                        )
                        st.session_state.edited_response = new_draft["body"]
                        st.rerun()
        
        # TAB 2: Entities
        with tab2:
            ner_data = result.get("pipeline", {}).get("ner", {}).get("data", {})
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.markdown('<div class="section-header">Pattern-Matched Entities</div>', unsafe_allow_html=True)
                patterns = ner_data.get("patterns", {})
                
                entity_categories = {
                    "Invoice IDs": patterns.get("invoice_ids", []),
                    "Account Numbers": patterns.get("account_numbers", []),
                    "Transaction IDs": patterns.get("transaction_ids", []),
                    "Amounts": patterns.get("amounts", []),
                    "Emails": patterns.get("email_addresses", []),
                    "Phones": patterns.get("phone_numbers", []),
                }
                
                for cat, items in entity_categories.items():
                    if items:
                        tags = "".join(f'<span class="entity-tag">{item}</span>' for item in items)
                        st.markdown(f"**{cat}**", unsafe_allow_html=False)
                        st.markdown(f'<div style="margin-bottom:12px;">{tags}</div>', unsafe_allow_html=True)
            
            with col_b:
                st.markdown('<div class="section-header">LLM-Extracted Entities</div>', unsafe_allow_html=True)
                llm_ents = ner_data.get("llm", {})
                
                display_fields = {
                    "Client Name": llm_ents.get("client_name"),
                    "Company": llm_ents.get("company_name"),
                    "Action Required": llm_ents.get("action_required"),
                }
                
                for label, value in display_fields.items():
                    if value:
                        st.markdown(f"""
                        <div class="info-row">
                            <span class="info-label">{label}</span>
                            <span class="info-value">{value}</span>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Due dates
                due_dates = llm_ents.get("due_dates", [])
                if due_dates:
                    st.markdown("**Due Dates**")
                    tags = "".join(f'<span class="entity-tag">{d}</span>' for d in due_dates)
                    st.markdown(f'<div>{tags}</div>', unsafe_allow_html=True)
                
                # Urgency indicators
                indicators = llm_ents.get("urgency_indicators", [])
                if indicators:
                    st.markdown("**Urgency Signals**")
                    tags = "".join(f'<span class="entity-tag" style="color:#FF8C00; border-color:rgba(255,140,0,0.3);">{i}</span>' for i in indicators)
                    st.markdown(f'<div>{tags}</div>', unsafe_allow_html=True)
        
        # TAB 3: Classification
        with tab3:
            clf = result.get("pipeline", {}).get("classification", {}).get("data", {})
            
            col_x, col_y = st.columns(2)
            
            with col_x:
                st.markdown('<div class="section-header">Classification Details</div>', unsafe_allow_html=True)
                
                fields = [
                    ("Urgency", clf.get("urgency", "—")),
                    ("Intent", clf.get("intent", "—").replace("_", " ")),
                    ("Confidence", f"{round(clf.get('confidence', 0) * 100)}%"),
                    ("Sentiment", clf.get("sentiment", "—")),
                    ("Requires Escalation", "Yes" if clf.get("requires_escalation") else "No"),
                ]
                
                for label, value in fields:
                    st.markdown(f"""
                    <div class="info-row">
                        <span class="info-label">{label}</span>
                        <span class="info-value">{value}</span>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col_y:
                st.markdown('<div class="section-header">LLM Reasoning</div>', unsafe_allow_html=True)
                reasoning = clf.get("reasoning", "No reasoning available")
                key_concern = clf.get("key_concern", "—")
                st.markdown(f"""
                <div class="response-box" style="font-size:13px;">
                    <strong style="color:#3B82F6;">Reasoning:</strong><br>
                    {reasoning}<br><br>
                    <strong style="color:#3B82F6;">Key Concern:</strong><br>
                    {key_concern}
                </div>
                """, unsafe_allow_html=True)
        
        # TAB 4: Raw Pipeline
        with tab4:
            st.markdown('<div class="section-header">Full Pipeline Output (JSON)</div>', unsafe_allow_html=True)
            st.json(result, expanded=False)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════════
elif "Analytics" in page:
    st.markdown("""
    <h1 style="font-size:28px; font-weight:600; color:#E8EAF0; margin-bottom:24px;">
        Analytics Dashboard
    </h1>
    """, unsafe_allow_html=True)
    
    history = st.session_state.triage_history
    
    if not history:
        st.info("No triage data yet. Run some messages through the Triage Center first.")
    else:
        # Summary metrics
        c1, c2, c3, c4 = st.columns(4)
        urgency_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for h in history:
            urgency_counts[h.get("urgency", "MEDIUM")] = urgency_counts.get(h.get("urgency", "MEDIUM"), 0) + 1
        
        with c1:
            st.metric("Total Triaged", len(history))
        with c2:
            st.metric("🔴 Critical", urgency_counts["CRITICAL"])
        with c3:
            st.metric("🟠 High", urgency_counts["HIGH"])
        with c4:
            avg = round(sum(h.get("processing_time_seconds", 0) for h in history) / len(history), 1)
            st.metric("Avg Process Time", f"{avg}s")
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            # Urgency distribution donut
            labels = list(urgency_counts.keys())
            values = list(urgency_counts.values())
            colors = ["#FF3B3B", "#FF8C00", "#FFD700", "#00C851"]
            
            fig = go.Figure(data=[go.Pie(
                labels=labels, values=values,
                hole=0.6, marker_colors=colors,
                textfont=dict(color="white")
            )])
            fig.update_layout(
                title=dict(text="Urgency Distribution", font=dict(color="#E8EAF0", size=14)),
                paper_bgcolor="#111827", plot_bgcolor="#111827",
                font=dict(color="#E8EAF0"),
                legend=dict(bgcolor="#111827"),
                margin=dict(t=50, b=20, l=20, r=20)
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col_chart2:
            # Intent breakdown bar chart
            intent_counts = {}
            for h in history:
                intent = h.get("intent", "UNKNOWN").replace("_", " ")
                intent_counts[intent] = intent_counts.get(intent, 0) + 1
            
            fig2 = px.bar(
                x=list(intent_counts.values()),
                y=list(intent_counts.keys()),
                orientation='h',
                color_discrete_sequence=["#3B82F6"],
            )
            fig2.update_layout(
                title=dict(text="Intent Breakdown", font=dict(color="#E8EAF0", size=14)),
                paper_bgcolor="#111827", plot_bgcolor="#111827",
                font=dict(color="#E8EAF0"),
                xaxis=dict(gridcolor="#1E2840"),
                yaxis=dict(gridcolor="#1E2840"),
                margin=dict(t=50, b=20, l=20, r=20),
                showlegend=False
            )
            st.plotly_chart(fig2, use_container_width=True)


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
    | Classification | llama-3.3-70b-versatile | Fast structured output |
    | NER Extraction | llama-3.3-70b-versatile | Speed priority |
    | Response Generation | llama-3.3-70b-versatile | Quality response |
    | Subject Line | llama-3.3-70b-versatile | Simple task |
    """)

    st.markdown('<div class="section-header" style="margin-top:24px;">Clear Data</div>', unsafe_allow_html=True)
    if st.button("🗑️ Clear Triage History (this session)", type="secondary"):
        st.session_state.triage_history = []
        st.session_state.current_result = None
        st.success("History cleared.")