import os
import streamlit as st
import pandas as pd
import httpx

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="LPDG Gateway Visit Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Professional styling: clean white/light background, corporate blue accents
st.markdown(
    """
    <style>
        .main-header {
            font-size: 2.1rem;
            font-weight: 700;
            color: #0F3D64;
            margin-bottom: 0.2rem;
        }
        .sub-header {
            font-size: 1.05rem;
            color: #4A5568;
            margin-bottom: 0.8rem;
        }
        .flow-pill {
            background-color: #EBF8FF;
            color: #2B6CB0;
            padding: 0.4rem 0.85rem;
            border-radius: 9999px;
            font-size: 0.85rem;
            font-weight: 600;
            border: 1px solid #BEE3F8;
            display: inline-block;
            margin-bottom: 1.2rem;
        }
        .status-box-online {
            background-color: #F0FFF4;
            color: #22543D;
            border: 1px solid #C6F6D5;
            padding: 0.6rem 1rem;
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.9rem;
            text-align: center;
        }
        .status-box-offline {
            background-color: #FFF5F5;
            color: #742A2A;
            border: 1px solid #FED7D7;
            padding: 0.6rem 1rem;
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.9rem;
            text-align: center;
        }
        .card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 10px;
            padding: 1.2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            margin-top: 0.5rem;
            margin-bottom: 1rem;
        }
        .card-title {
            font-size: 1.15rem;
            font-weight: 600;
            color: #1A365D;
            margin-bottom: 0.6rem;
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
# API Helper Functions (Consumes FastAPI via HTTP)
# ---------------------------------------------------------
def check_api_health() -> tuple[bool, dict]:
    try:
        with httpx.Client(timeout=3.0) as client:
            resp = client.get(f"{API_BASE_URL}/health")
            if resp.status_code == 200:
                return True, resp.json()
            return False, {"detail": f"Status code: {resp.status_code}"}
    except Exception as e:
        return False, {"detail": f"FastAPI service not reachable at {API_BASE_URL}. Please start uvicorn src.api.main:app --reload (Error: {e})"}


def fetch_week_rankings(week_start: str) -> tuple[int, dict | list]:
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{API_BASE_URL}/weeks/{week_start}/rankings")
            return resp.status_code, resp.json()
    except Exception as e:
        return 0, {"detail": f"FastAPI service not reachable at {API_BASE_URL}. Please start uvicorn src.api.main:app --reload (Error: {e})"}


def fetch_gateway_explanation(gateway_id: str, week_start: str) -> tuple[int, dict]:
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(
                f"{API_BASE_URL}/gateways/{gateway_id}/explanation",
                params={"week_start": week_start},
            )
            return resp.status_code, resp.json()
    except Exception as e:
        return 0, {"detail": f"FastAPI service not reachable at {API_BASE_URL}. Please start uvicorn src.api.main:app --reload (Error: {e})"}


def trigger_rerun(week_start: str | None = None) -> tuple[int, dict]:
    try:
        with httpx.Client(timeout=15.0) as client:
            payload = {"week_start": week_start} if week_start else {}
            resp = client.post(f"{API_BASE_URL}/run", json=payload)
            return resp.status_code, resp.json()
    except Exception as e:
        return 0, {"detail": f"FastAPI service not reachable at {API_BASE_URL}. Please start uvicorn src.api.main:app --reload (Error: {e})"}


# ---------------------------------------------------------
# Header & Architecture Workflow
# ---------------------------------------------------------
col_header, col_status = st.columns([3, 1])

with col_header:
    st.markdown('<div class="main-header">LPDG Gateway Visit Dashboard</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Prioritized field visits for radio smart-meter gateways based on 3-sigma telemetry anomaly analysis.</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="flow-pill">User &rarr; Streamlit Dashboard &rarr; FastAPI &rarr; RankingEngine &rarr; Telemetry Data</div>',
        unsafe_allow_html=True,
    )

with col_status:
    is_online, health_data = check_api_health()
    if is_online:
        st.markdown(
            f'<div class="status-box-online">🟢 API Online &bull; v{health_data.get("version", "1.0.0")}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="status-box-offline">🔴 API Offline &bull; Not Connected</div>',
            unsafe_allow_html=True,
        )
        st.caption(f"Target: `{API_BASE_URL}`")

if not is_online:
    st.warning(
        f"⚠️ **FastAPI service not reachable at {API_BASE_URL}**.\n\n"
        "Please open your terminal and start the backend service with:\n"
        "```powershell\n"
        "uvicorn src.api.main:app --reload\n"
        "```"
    )

# ---------------------------------------------------------
# Controls: Week Selection & Action Buttons
# ---------------------------------------------------------
ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns([2, 1.2, 1.2, 2.5])

with ctrl_col1:
    selected_week = st.selectbox(
        "Select Scored Week:",
        options=SCORED_WEEKS,
        index=0,
        help="Choose one of the eight scored deployment Mondays from Feb 2 to Mar 23, 2026.",
    )

with ctrl_col2:
    st.write("")
    st.write("")
    load_btn = st.button("📥 Load Rankings", use_container_width=True, type="primary")

with ctrl_col3:
    st.write("")
    st.write("")
    run_btn = st.button("🔄 Run Again", use_container_width=True)

with ctrl_col4:
    st.write("")
    st.write("")
    run_all_check = st.checkbox("Run for all 8 weeks on 'Run Again'", value=False)

# Session state initialization
if "rankings_data" not in st.session_state:
    st.session_state.rankings_data = None
if "current_week" not in st.session_state:
    st.session_state.current_week = selected_week

# Auto-load on initial view if API is available and state is empty
if st.session_state.rankings_data is None and is_online:
    status_code, response_data = fetch_week_rankings(selected_week)
    if status_code == 200:
        st.session_state.rankings_data = response_data.get("gateways", [])
        st.session_state.current_week = selected_week

# Handle Load Rankings action
if load_btn:
    with st.spinner(f"Querying FastAPI for week {selected_week}..."):
        status_code, response_data = fetch_week_rankings(selected_week)
        if status_code == 200:
            st.session_state.rankings_data = response_data.get("gateways", [])
            st.session_state.current_week = selected_week
            st.success(f"Successfully loaded top 15 gateways for week {selected_week}.")
        elif status_code == 0:
            st.error(f"⚠️ {response_data.get('detail')}")
        elif status_code == 400:
            st.error(f"Bad Request (HTTP 400): {response_data.get('detail')}")
        elif status_code == 404:
            st.error(f"Not Found (HTTP 404): {response_data.get('detail')}")
        elif status_code == 500:
            st.error(f"API Server Error (HTTP 500): {response_data.get('detail')}")
        else:
            st.error(f"Failed to fetch rankings (HTTP {status_code}): {response_data.get('detail')}")

# Handle Run Again action
if run_btn:
    week_arg = None if run_all_check else selected_week
    with st.spinner("Triggering calculation on FastAPI via POST /run..."):
        status_code, response_data = trigger_rerun(week_arg)
        if status_code == 200:
            st.success(f"Success: {response_data.get('message')}")
            _, fresh_data = fetch_week_rankings(selected_week)
            if isinstance(fresh_data, dict) and "gateways" in fresh_data:
                st.session_state.rankings_data = fresh_data.get("gateways", [])
                st.session_state.current_week = selected_week
        elif status_code == 0:
            st.error(f"⚠️ {response_data.get('detail')}")
        else:
            st.error(f"Run failed (HTTP {status_code}): {response_data.get('detail')}")

# ---------------------------------------------------------
# Summary / Metrics Row
# ---------------------------------------------------------
st.markdown("---")
m_col1, m_col2, m_col3 = st.columns(3)

with m_col1:
    ranked_count = len(st.session_state.rankings_data) if st.session_state.rankings_data else 0
    st.metric(label="Total Ranked Gateways", value=f"{ranked_count} Gateways", delta="Fixed Capacity: 15" if ranked_count == 15 else None)

with m_col2:
    st.metric(label="Selected Week", value=st.session_state.current_week or selected_week)

with m_col3:
    status_label = "Online (Connected)" if is_online else "Offline (Unreachable)"
    st.metric(label="API Connection Status", value=status_label)

# ---------------------------------------------------------
# Display Rankings Table
# ---------------------------------------------------------
st.markdown("---")

if st.session_state.rankings_data:
    gateways_list = st.session_state.rankings_data
    df = pd.DataFrame(gateways_list)

    table_df = pd.DataFrame(
        {
            "Rank": df["rank"].astype(int),
            "Gateway ID": df["gateway_id"].astype(str),
            "Score": df["score"].astype(float),
            "Reason": df["reason"].astype(str),
        }
    )

    st.subheader(f"Top 15 Gateways for Week {st.session_state.current_week}")
    st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Rank": st.column_config.NumberColumn("Rank", format="%d", width="small"),
            "Gateway ID": st.column_config.TextColumn("Gateway ID", width="medium"),
            "Score": st.column_config.NumberColumn("Score (Breach Hours)", format="%.1f", width="small"),
            "Reason": st.column_config.TextColumn("Reason", width="large"),
        },
    )

    # ---------------------------------------------------------
    # Gateway Explanation Section
    # ---------------------------------------------------------
    st.markdown("---")
    st.subheader("Gateway Diagnosis & Explanation")
    st.caption("Inspect why a specific gateway is ranked, or query any gateway across the wider network.")

    exp_col1, exp_col2 = st.columns([1.5, 2.5])

    available_ids = [gw["gateway_id"] for gw in gateways_list]

    with exp_col1:
        id_mode = st.radio(
            "Select lookup method:",
            options=["From this week's top 15", "Enter custom Gateway ID"],
            horizontal=True,
        )

        if id_mode == "From this week's top 15":
            target_gw = st.selectbox("Select Gateway ID:", options=available_ids)
        else:
            target_gw = st.text_input("Enter Gateway ID (e.g. 0A2778A31BE3):", value=available_ids[0] if available_ids else "0A2778A31BE3")

        explain_btn = st.button("🔍 Explain Gateway", use_container_width=True)

    with exp_col2:
        if explain_btn or target_gw:
            if target_gw:
                code, exp_data = fetch_gateway_explanation(target_gw.strip(), st.session_state.current_week)
                if code == 200:
                    in_top = exp_data.get("in_top_15", False)
                    badge = "✅ Priority Site Visit Recommended (Top 15)" if in_top else "ℹ️ Outside Top 15 (No Visit Required)"
                    rank_display = f"#{exp_data.get('rank')}" if exp_data.get("rank") is not None else "Unranked"

                    st.markdown(
                        f"""
                        <div class="card">
                            <div class="card-title">Diagnosis for Gateway <code>{exp_data.get('gateway_id')}</code> ({st.session_state.current_week})</div>
                            <p style="margin-bottom: 0.5rem;"><strong>Status:</strong> {badge}</p>
                            <p style="margin-bottom: 0.5rem;"><strong>Rank:</strong> {rank_display} &bull; <strong>Score:</strong> {exp_data.get('score')} breach hour(s)</p>
                            <p style="margin-bottom: 0;"><strong>Audit Rationale:</strong> {exp_data.get('reason')}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                elif code == 0:
                    st.error(f"⚠️ {exp_data.get('detail')}")
                elif code == 404:
                    st.error(f"Gateway Not Found (HTTP 404): {exp_data.get('detail')}")
                elif code == 400:
                    st.error(f"Bad Request (HTTP 400): {exp_data.get('detail')}")
                elif code == 500:
                    st.error(f"API Server Error (HTTP 500): {exp_data.get('detail')}")
                else:
                    st.error(f"Error (HTTP {code}): {exp_data.get('detail')}")
            else:
                st.info("Please enter or select a gateway ID to explain.")
else:
    if is_online:
        st.info("Click 'Load Rankings' above to display the weekly gateway recommendations.")
