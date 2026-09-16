import os
import streamlit as st
import pandas as pd
import httpx

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="LPDG Gateway Intelligence | Field Visit Prioritization",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------
# Enterprise CSS Styling
# ---------------------------------------------------------
st.markdown(
    """
    <style>
        /* Global Page Adjustments */
        .block-container {
            max-width: 1260px !important;
            padding-top: 1.5rem !important;
            padding-bottom: 3rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }
        
        /* Modern Header Hero */
        .hero-banner {
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #0F3D64 100%);
            border-radius: 14px;
            padding: 1.75rem 2rem;
            color: #FFFFFF;
            margin-bottom: 1.5rem;
            box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.15), 0 8px 10px -6px rgba(15, 23, 42, 0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }
        .hero-title-group h1 {
            font-size: 1.85rem !important;
            font-weight: 700 !important;
            color: #FFFFFF !important;
            margin: 0 !important;
            letter-spacing: -0.02em;
            display: flex;
            align-items: center;
            gap: 0.6rem;
        }
        .hero-title-group p {
            font-size: 0.95rem;
            color: #94A3B8;
            margin: 0.35rem 0 0 0;
        }
        .hero-badge-container {
            display: flex;
            gap: 0.6rem;
            align-items: center;
        }
        .badge-online {
            background: rgba(16, 185, 129, 0.15);
            color: #34D399;
            border: 1px solid rgba(52, 211, 153, 0.4);
            padding: 0.4rem 0.9rem;
            border-radius: 9999px;
            font-size: 0.85rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.45rem;
        }
        .badge-offline {
            background: rgba(239, 68, 68, 0.15);
            color: #F87171;
            border: 1px solid rgba(248, 113, 113, 0.4);
            padding: 0.4rem 0.9rem;
            border-radius: 9999px;
            font-size: 0.85rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.45rem;
        }
        .badge-track {
            background: rgba(59, 130, 246, 0.15);
            color: #60A5FA;
            border: 1px solid rgba(96, 165, 250, 0.3);
            padding: 0.4rem 0.85rem;
            border-radius: 9999px;
            font-size: 0.85rem;
            font-weight: 600;
        }

        /* Architecture Process Stepper */
        .pipeline-box {
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 10px;
            padding: 0.75rem 1.25rem;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 0.85rem;
            color: #475569;
            flex-wrap: wrap;
            gap: 0.5rem;
        }
        .pipeline-step {
            display: flex;
            align-items: center;
            gap: 0.4rem;
            font-weight: 600;
        }
        .step-active {
            color: #2563EB;
        }
        .pipeline-arrow {
            color: #94A3B8;
            font-weight: 700;
        }

        /* Metric Cards */
        .metric-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 1.15rem 1.25rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
            transition: all 0.2s ease;
        }
        .metric-card:hover {
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08);
            border-color: #CBD5E1;
        }
        .metric-label {
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #64748B;
            font-weight: 600;
            margin-bottom: 0.25rem;
        }
        .metric-value {
            font-size: 1.65rem;
            font-weight: 700;
            color: #0F172A;
            line-height: 1.2;
        }
        .metric-sub {
            font-size: 0.8rem;
            color: #2563EB;
            font-weight: 500;
            margin-top: 0.35rem;
        }

        /* Modern Filter Panel */
        .control-panel {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 1.25rem 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
        }

        /* Buttons Styling Overrides */
        div.stButton > button:first-child {
            background-color: #2563EB;
            color: white;
            font-weight: 600;
            border-radius: 8px;
            border: none;
            padding: 0.55rem 1.25rem;
            transition: all 0.2s ease;
        }
        div.stButton > button:first-child:hover {
            background-color: #1D4ED8;
            color: white;
            border: none;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
        }

        /* Custom HTML Table */
        .styled-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            margin-top: 0.75rem;
            background: #FFFFFF;
            border-radius: 10px;
            overflow: hidden;
            border: 1px solid #E2E8F0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }
        .styled-table thead tr {
            background-color: #F8FAFC;
            color: #475569;
            text-align: left;
            font-size: 0.82rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .styled-table th, .styled-table td {
            padding: 12px 16px;
            border-bottom: 1px solid #F1F5F9;
        }
        .styled-table tbody tr:last-child td {
            border-bottom: none;
        }
        .styled-table tbody tr:hover {
            background-color: #F8FAFC;
        }
        
        .rank-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 28px;
            height: 28px;
            border-radius: 9999px;
            font-weight: 700;
            font-size: 0.85rem;
        }
        .rank-1 { background-color: #FEF3C7; color: #B45309; border: 1px solid #FDE68A; }
        .rank-2 { background-color: #F1F5F9; color: #475569; border: 1px solid #E2E8F0; }
        .rank-3 { background-color: #FFEDD5; color: #C2410C; border: 1px solid #FED7AA; }
        .rank-other { background-color: #EFF6FF; color: #1E40AF; border: 1px solid #DBEAFE; }

        .gw-mono {
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 0.88rem;
            font-weight: 600;
            color: #0F172A;
            background: #F1F5F9;
            padding: 3px 8px;
            border-radius: 5px;
            border: 1px solid #E2E8F0;
        }
        .score-pill {
            display: inline-block;
            background: #FEF2F2;
            color: #B91C1C;
            border: 1px solid #FEE2E2;
            padding: 2px 10px;
            border-radius: 9999px;
            font-weight: 700;
            font-size: 0.85rem;
        }
        .reason-text {
            font-size: 0.88rem;
            color: #334155;
            line-height: 1.4;
        }
        .metric-tag {
            font-weight: 600;
            color: #1E40AF;
            background: #EFF6FF;
            padding: 1px 6px;
            border-radius: 4px;
        }

        /* Diagnosis Card */
        .diag-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        }
        .diag-title {
            font-size: 1.2rem;
            font-weight: 700;
            color: #0F172A;
            margin-bottom: 0.75rem;
        }
        .priority-badge-visit {
            background: #ECFDF5;
            color: #047857;
            border: 1px solid #A7F3D0;
            padding: 0.35rem 0.85rem;
            border-radius: 6px;
            font-weight: 600;
            font-size: 0.85rem;
            display: inline-block;
            margin-bottom: 1rem;
        }
        .priority-badge-novisit {
            background: #F1F5F9;
            color: #475569;
            border: 1px solid #E2E8F0;
            padding: 0.35rem 0.85rem;
            border-radius: 6px;
            font-weight: 600;
            font-size: 0.85rem;
            display: inline-block;
            margin-bottom: 1rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# Configuration & Constants
# ---------------------------------------------------------
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

SCORED_WEEKS = [
    "2026-02-02",
    "2026-02-09",
    "2026-02-16",
    "2026-02-23",
    "2026-03-02",
    "2026-03-09",
    "2026-03-16",
    "2026-03-23",
]


# ---------------------------------------------------------
# API Helper Functions (Pure HTTP Client)
# ---------------------------------------------------------
@st.cache_data(ttl=2.0)
def check_api_health() -> tuple[bool, dict]:
    try:
        with httpx.Client(timeout=2.5) as client:
            resp = client.get(f"{API_BASE_URL}/health")
            if resp.status_code == 200:
                return True, resp.json()
            return False, {"detail": f"HTTP {resp.status_code}"}
    except Exception as e:
        return False, {"detail": str(e)}


def fetch_week_rankings(week_start: str) -> tuple[int, dict]:
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{API_BASE_URL}/weeks/{week_start}/rankings")
            return resp.status_code, resp.json()
    except Exception as e:
        return 0, {"detail": f"FastAPI service unreachable at {API_BASE_URL}: {e}"}


def fetch_gateway_explanation(gateway_id: str, week_start: str) -> tuple[int, dict]:
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(
                f"{API_BASE_URL}/gateways/{gateway_id}/explanation",
                params={"week_start": week_start},
            )
            return resp.status_code, resp.json()
    except Exception as e:
        return 0, {"detail": f"FastAPI service unreachable at {API_BASE_URL}: {e}"}


def trigger_rerun(week_start: str | None = None) -> tuple[int, dict]:
    try:
        with httpx.Client(timeout=15.0) as client:
            payload = {"week_start": week_start} if week_start else {}
            resp = client.post(f"{API_BASE_URL}/run", json=payload)
            return resp.status_code, resp.json()
    except Exception as e:
        return 0, {"detail": f"FastAPI service unreachable at {API_BASE_URL}: {e}"}


# ---------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------
if "selected_week" not in st.session_state:
    st.session_state.selected_week = SCORED_WEEKS[0]
if "rankings_data" not in st.session_state:
    st.session_state.rankings_data = None
if "last_loaded_week" not in st.session_state:
    st.session_state.last_loaded_week = None

# Check API Health
is_online, health_info = check_api_health()

# ---------------------------------------------------------
# Hero Header Banner
# ---------------------------------------------------------
status_badge_html = (
    f'<div class="badge-online"><span>●</span> API Online v{health_info.get("version", "1.0.0")}</div>'
    if is_online
    else '<div class="badge-offline"><span>●</span> API Offline</div>'
)

st.markdown(
    f"""
    <div class="hero-banner">
        <div class="hero-title-group">
            <h1>⚡ LPDG Gateway Visit Dashboard</h1>
            <p>Automated 3-sigma anomaly prioritization for smart meter radio gateways • Operations Triage Console</p>
        </div>
        <div class="hero-badge-container">
            <div class="badge-track">Track B • Software Dev</div>
            {status_badge_html}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# Architecture Pipeline Breadcrumb
# ---------------------------------------------------------
st.markdown(
    """
    <div class="pipeline-box">
        <div class="pipeline-step"><span class="step-active">1. 📡 Telemetry Ingestion</span></div>
        <span class="pipeline-arrow">&rarr;</span>
        <div class="pipeline-step"><span class="step-active">2. ⚙️ 28-Day Baseline (3&sigma;)</span></div>
        <span class="pipeline-arrow">&rarr;</span>
        <div class="pipeline-step"><span class="step-active">3. ⚡ FastAPI Service (:8000)</span></div>
        <span class="pipeline-arrow">&rarr;</span>
        <div class="pipeline-step"><span class="step-active">4. 📊 Streamlit Ops Dashboard (:8501)</span></div>
        <span class="pipeline-arrow">&rarr;</span>
        <div class="pipeline-step"><span>🛠️ Field Crew Dispatch</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Offline Warning Banner
if not is_online:
    st.warning(
        f"⚠️ **FastAPI backend is unreachable at `{API_BASE_URL}`.**\n\n"
        "To start the API service, open your terminal and run:\n"
        "```powershell\nuvicorn src.api.main:app --reload\n```"
    )

# ---------------------------------------------------------
# Control Panel (Card Layout)
# ---------------------------------------------------------
st.markdown('<div class="control-panel">', unsafe_allow_html=True)
c_col1, c_col2, c_col3, c_col4 = st.columns([2.2, 1.4, 1.4, 2.5], gap="medium")

with c_col1:
    selected_week = st.selectbox(
        "Scored Deployment Monday:",
        options=SCORED_WEEKS,
        index=SCORED_WEEKS.index(st.session_state.selected_week) if st.session_state.selected_week in SCORED_WEEKS else 0,
        help="Select one of the 8 scored Mondays from 2026-02-02 to 2026-03-23.",
    )
    st.session_state.selected_week = selected_week

with c_col2:
    st.write("")
    st.write("")
    load_btn = st.button("📥 Load Rankings", use_container_width=True)

with c_col3:
    st.write("")
    st.write("")
    run_btn = st.button("🔄 Recompute", use_container_width=True)

with c_col4:
    st.write("")
    st.write("")
    run_all_check = st.checkbox("Recompute all 8 weeks on 'Recompute'", value=False)

st.markdown('</div>', unsafe_allow_html=True)

# Auto-load data if not already loaded
if st.session_state.rankings_data is None and is_online:
    code, resp = fetch_week_rankings(selected_week)
    if code == 200:
        st.session_state.rankings_data = resp.get("gateways", [])
        st.session_state.last_loaded_week = selected_week

# Process Load Rankings click
if load_btn:
    with st.spinner(f"Fetching rankings for week {selected_week} from FastAPI..."):
        code, resp = fetch_week_rankings(selected_week)
        if code == 200:
            st.session_state.rankings_data = resp.get("gateways", [])
            st.session_state.last_loaded_week = selected_week
            st.toast(f"✅ Loaded {len(st.session_state.rankings_data)} gateways for {selected_week}", icon="📋")
        else:
            st.error(f"Error ({code}): {resp.get('detail', 'Unknown error')}")

# Process Recompute click
if run_btn:
    week_param = None if run_all_check else selected_week
    with st.spinner("Invoking POST /run on FastAPI..."):
        code, resp = trigger_rerun(week_param)
        if code == 200:
            st.success(f"Calculation complete: {resp.get('message')}")
            # Refresh current week
            _, fresh_resp = fetch_week_rankings(selected_week)
            if isinstance(fresh_resp, dict) and "gateways" in fresh_resp:
                st.session_state.rankings_data = fresh_resp.get("gateways", [])
                st.session_state.last_loaded_week = selected_week
        else:
            st.error(f"Failed (HTTP {code}): {resp.get('detail')}")

# ---------------------------------------------------------
# Dynamic KPI Cards Row
# ---------------------------------------------------------
current_list = st.session_state.rankings_data or []
top_score = f"{current_list[0]['score']:.1f} hrs" if current_list else "—"
active_week_str = st.session_state.last_loaded_week or selected_week
top_reason_metric = "disconnection_cnt"
if current_list and "offline_duration" in current_list[0].get("reason", ""):
    top_reason_metric = "offline_duration"

kpi1, kpi2, kpi3, kpi4 = st.columns(4, gap="medium")

with kpi1:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Visit Quota</div>
            <div class="metric-value">{len(current_list)} / 15</div>
            <div class="metric-sub">✓ 100% capacity scheduled</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with kpi2:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Selected Week</div>
            <div class="metric-value" style="font-size: 1.35rem; padding-top: 0.2rem;">{active_week_str}</div>
            <div class="metric-sub">Trailing 28d baseline window</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with kpi3:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">Max Anomaly Score</div>
            <div class="metric-value">{top_score}</div>
            <div class="metric-sub">Rank #1 worst deviation</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with kpi4:
    status_text = "Connected (:8000)" if is_online else "Offline"
    status_color = "#10B981" if is_online else "#EF4444"
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">FastAPI Backend</div>
            <div class="metric-value" style="color: {status_color}; font-size: 1.35rem; padding-top: 0.2rem;">{status_text}</div>
            <div class="metric-sub">REST /docs Swagger active</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.write("")

# ---------------------------------------------------------
# Tabbed Workspace
# ---------------------------------------------------------
tab_schedule, tab_diag, tab_arch = st.tabs([
    "📋 Weekly Visit Schedule (Top 15)",
    "🔍 Gateway Diagnostic Audit",
    "🏗️ System Architecture & API",
])

# ---------------------------------------------------------
# TAB 1: Weekly Visit Schedule Table
# ---------------------------------------------------------
with tab_schedule:
    if current_list:
        st.markdown(f"#### Prioritized Field Visits for Scored Week: `{active_week_str}`")
        st.caption("Exactly 15 radio gateways prioritized for field technician visits based on trailing 7-day 3-sigma telemetry deviations.")

        # Build custom styled HTML table
        table_rows = []
        for gw in current_list:
            rank = gw["rank"]
            gw_id = gw["gateway_id"]
            score = gw["score"]
            reason = gw["reason"]

            # Rank Badge Class
            if rank == 1:
                rank_badge = f'<span class="rank-badge rank-1">1</span>'
            elif rank == 2:
                rank_badge = f'<span class="rank-badge rank-2">2</span>'
            elif rank == 3:
                rank_badge = f'<span class="rank-badge rank-3">3</span>'
            else:
                rank_badge = f'<span class="rank-badge rank-other">{rank}</span>'

            # Format reason with highlighted metric tag
            highlighted_reason = reason
            for metric_kw in ["disconnection_cnt", "offline_duration_sec", "reboot_cnt"]:
                if metric_kw in highlighted_reason:
                    highlighted_reason = highlighted_reason.replace(
                        metric_kw, f'<span class="metric-tag">{metric_kw}</span>'
                    )

            table_rows.append(
                f"""
                <tr>
                    <td style="width: 70px; text-align: center;">{rank_badge}</td>
                    <td style="width: 170px;"><span class="gw-mono">{gw_id}</span></td>
                    <td style="width: 150px;"><span class="score-pill">{score:.1f} hrs</span></td>
                    <td class="reason-text">{highlighted_reason}</td>
                </tr>
                """
            )

        html_table = f"""
        <table class="styled-table">
            <thead>
                <tr>
                    <th style="width: 70px; text-align: center;">Rank</th>
                    <th style="width: 170px;">Gateway ID</th>
                    <th style="width: 150px;">Anomaly Score</th>
                    <th>Diagnostic Audit Reason</th>
                </tr>
            </thead>
            <tbody>
                {''.join(table_rows)}
            </tbody>
        </table>
        """
        st.markdown(html_table, unsafe_allow_html=True)

        st.write("")
        # CSV Export action
        csv_df = pd.DataFrame(current_list)
        csv_data = csv_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Export This Week's Visit Schedule (CSV)",
            data=csv_data,
            file_name=f"lpdg_visits_{active_week_str}.csv",
            mime="text/csv",
        )
    else:
        if is_online:
            st.info("Click 'Load Rankings' above to fetch the weekly gateway recommendations.")
        else:
            st.error("Cannot load rankings because the FastAPI backend is offline. Please start uvicorn.")

# ---------------------------------------------------------
# TAB 2: Gateway Diagnostic Audit Deep-Dive
# ---------------------------------------------------------
with tab_diag:
    st.markdown("#### Individual Gateway Diagnostic Deep-Dive")
    st.caption("Inspect why a specific gateway breached its statistical threshold, or audit any gateway across the wider network.")

    d_col1, d_col2 = st.columns([1.5, 2.5], gap="large")

    with d_col1:
        st.markdown('<div style="background: #F8FAFC; border: 1px solid #E2E8F0; padding: 1.25rem; border-radius: 10px;">', unsafe_allow_html=True)
        id_source = st.radio(
            "Select Gateway Source:",
            options=["From this week's top 15", "Enter custom Gateway ID"],
            horizontal=False,
        )

        available_ids = [gw["gateway_id"] for gw in current_list] if current_list else ["0A2778A31BE3"]

        if id_source == "From this week's top 15" and available_ids:
            target_id = st.selectbox("Target Gateway ID:", options=available_ids)
        else:
            target_id = st.text_input("Enter Gateway ID (12-char hex):", value="0A2778A31BE3")

        audit_btn = st.button("🔍 Run Diagnostic Audit", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with d_col2:
        if audit_btn or target_id:
            cleaned_id = target_id.strip().upper()
            code, exp = fetch_gateway_explanation(cleaned_id, active_week_str)

            if code == 200:
                in_top = exp.get("in_top_15", False)
                rank_str = f"#{exp.get('rank')}" if exp.get("rank") is not None else "Unranked"
                score_str = f"{exp.get('score')} hrs" if exp.get("score") is not None else "0.0 hrs"

                badge_markup = (
                    '<div class="priority-badge-visit">✓ Priority Physical Visit Recommended (Ranked in Top 15)</div>'
                    if in_top
                    else '<div class="priority-badge-novisit">ℹ️ Normal Operation • Outside Top 15 (No Visit Required)</div>'
                )

                st.markdown(
                    f"""
                    <div class="diag-card">
                        <div class="diag-title">Audit Report: Gateway <code style="color: #2563EB;">{exp.get('gateway_id')}</code></div>
                        {badge_markup}
                        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; margin-bottom: 1.25rem;">
                            <div style="background: #F8FAFC; padding: 0.75rem; border-radius: 8px; border: 1px solid #E2E8F0;">
                                <div style="font-size: 0.75rem; color: #64748B; font-weight: 600;">ASSIGNED RANK</div>
                                <div style="font-size: 1.25rem; font-weight: 700; color: #0F172A;">{rank_str}</div>
                            </div>
                            <div style="background: #F8FAFC; padding: 0.75rem; border-radius: 8px; border: 1px solid #E2E8F0;">
                                <div style="font-size: 0.75rem; color: #64748B; font-weight: 600;">3-SIGMA BREACH</div>
                                <div style="font-size: 1.25rem; font-weight: 700; color: #B91C1C;">{score_str}</div>
                            </div>
                            <div style="background: #F8FAFC; padding: 0.75rem; border-radius: 8px; border: 1px solid #E2E8F0;">
                                <div style="font-size: 0.75rem; color: #64748B; font-weight: 600;">DISPATCH COST</div>
                                <div style="font-size: 1.25rem; font-weight: 700; color: #0F172A;">{"£380" if in_top else "£0 (Saved)"}</div>
                            </div>
                        </div>
                        <div style="font-size: 0.85rem; color: #64748B; font-weight: 600; margin-bottom: 0.35rem;">AUDIT RATIONALE</div>
                        <p style="font-size: 0.95rem; color: #1E293B; background: #F1F5F9; padding: 0.85rem 1rem; border-radius: 8px; line-height: 1.5; border: 1px solid #E2E8F0; margin: 0;">
                            {exp.get('reason')}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            elif code == 404:
                st.error(f"Gateway Not Found (HTTP 404): {exp.get('detail')}")
            elif code == 400:
                st.error(f"Bad Request (HTTP 400): {exp.get('detail')}")
            else:
                st.error(f"Error ({code}): {exp.get('detail', 'Unknown error')}")

# ---------------------------------------------------------
# TAB 3: System Architecture & API
# ---------------------------------------------------------
with tab_arch:
    st.markdown("#### System Architecture & Decoupled Design")
    st.caption("Strict separation between ingestion mathematics, REST service layer, and client presentations.")

    arch_col1, arch_col2 = st.columns([1.6, 1.4], gap="large")

    with arch_col1:
        st.markdown(
            """
            ```
             ┌─────────────────────────────────────────────────────────┐
             │       Streamlit Dashboard (Port 8501 - Presentation)    │
             └────────────────────────────┬────────────────────────────┘
                                          │ HTTP REST (httpx)
                                          ▼
             ┌─────────────────────────────────────────────────────────┐
             │       FastAPI Application (Port 8000 - Service Layer)   │
             │   - /health                                             │
             │   - /weeks/{week_start}/rankings                        │
             │   - /gateways/{gateway_id}/explanation                  │
             │   - /run (POST)                                         │
             └────────────────────────────┬────────────────────────────┘
                                          │ Strategy Pattern
                                          ▼
             ┌─────────────────────────────────────────────────────────┐
             │       RankingEngine (src/ranking/engine.py)             │
             │   - Pluggable RankingStrategy Protocol                  │
             │   - ThreeSigmaStrategy (Baseline) / CustomMLStrategy   │
             └────────────────────────────┬────────────────────────────┘
                                          │ Disk I/O
                                          ▼
             ┌─────────────────────────────────────────────────────────┐
             │   Telemetry Data (data/telemetry/ or predictions.csv)   │
             └─────────────────────────────────────────────────────────┘
            ```
            """
        )

    with arch_col2:
        st.markdown(
            """
            ##### Live API Endpoints
            - `GET /health`: Healthcheck, version, data availability
            - `GET /weeks/{date}/rankings`: Returns 15 prioritized gateways
            - `GET /gateways/{id}/explanation`: 3-sigma anomaly rationale
            - `POST /run`: On-demand calculation & predictions.csv export

            ##### Key Engineering Highlights
            - **Strategy Pattern:** Seamlessly swap 3-sigma baseline for ML models without touching API or UI.
            - **No Logic Duplication:** Dashboard performs zero ranking math; all results arrive via FastAPI.
            - **Fail-Safe Robustness:** Clean HTTP 400/404/422/500 error propagation with zero Python traceback leakage.
            """
        )
