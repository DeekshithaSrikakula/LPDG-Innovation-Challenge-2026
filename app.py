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
# API Helper Functions (Consumes FastAPI over HTTP)
# ---------------------------------------------------------
def check_api_health() -> tuple[bool, dict]:
    try:
        with httpx.Client(timeout=3.0) as client:
            resp = client.get(f"{API_BASE_URL}/health")
            if resp.status_code == 200:
                return True, resp.json()
            return False, {"detail": f"Status code: {resp.status_code}"}
    except Exception as e:
        return False, {"detail": f"FastAPI service not reachable at {API_BASE_URL}: {e}"}


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

is_online, health_data = check_api_health()

# ---------------------------------------------------------
# Header & Architecture
# ---------------------------------------------------------
header_col1, header_col2 = st.columns([3.5, 1.2])

with header_col1:
    st.title("⚡ LPDG Gateway Visit Dashboard")
    st.markdown("**Prioritized field visit recommendations for radio smart-meter gateways based on 3-sigma telemetry anomalies.**")

with header_col2:
    st.write("")
    if is_online:
        st.success(f"🟢 API Online • v{health_data.get('version', '1.0.0')}")
    else:
        st.error("🔴 API Offline • Not Connected")

# Decoupled Architecture Banner
st.info("🔄 **Architecture Flow:** User → Streamlit Dashboard (:8501) → FastAPI REST Service (:8000) → RankingEngine → Telemetry Data")

if not is_online:
    st.warning(
        f"⚠️ **FastAPI backend is unreachable at `{API_BASE_URL}`.**\n\n"
        "To start the API service, open your terminal and run:\n"
        "```powershell\nuvicorn src.api.main:app --reload\n```"
    )

# ---------------------------------------------------------
# Control Panel
# ---------------------------------------------------------
with st.container():
    c_col1, c_col2, c_col3, c_col4 = st.columns([2.2, 1.3, 1.3, 2.5])

    with c_col1:
        selected_week = st.selectbox(
            "Select Scored Week:",
            options=SCORED_WEEKS,
            index=SCORED_WEEKS.index(st.session_state.selected_week) if st.session_state.selected_week in SCORED_WEEKS else 0,
            help="Choose one of the eight scored deployment Mondays from Feb 2 to Mar 23, 2026.",
        )
        st.session_state.selected_week = selected_week

    with c_col2:
        st.write("")
        st.write("")
        load_btn = st.button("📥 Load Rankings", use_container_width=True, type="primary")

    with c_col3:
        st.write("")
        st.write("")
        run_btn = st.button("🔄 Recompute", use_container_width=True)

    with c_col4:
        st.write("")
        st.write("")
        run_all_check = st.checkbox("Recompute all 8 weeks on 'Recompute'", value=False)

# Auto-load on initial view if API is available and state is empty
if st.session_state.rankings_data is None and is_online:
    code, resp = fetch_week_rankings(selected_week)
    if code == 200:
        st.session_state.rankings_data = resp.get("gateways", [])
        st.session_state.last_loaded_week = selected_week

# Handle Load Rankings action
if load_btn:
    with st.spinner(f"Querying FastAPI for week {selected_week}..."):
        code, resp = fetch_week_rankings(selected_week)
        if code == 200:
            st.session_state.rankings_data = resp.get("gateways", [])
            st.session_state.last_loaded_week = selected_week
            st.toast(f"Loaded rankings for {selected_week}", icon="✅")
        elif code == 0:
            st.error(resp.get("detail"))
        else:
            st.error(f"Error (HTTP {code}): {resp.get('detail')}")

# Handle Recompute action
if run_btn:
    week_arg = None if run_all_check else selected_week
    with st.spinner("Triggering ranking calculation via POST /run..."):
        code, resp = trigger_rerun(week_arg)
        if code == 200:
            st.success(f"Success: {resp.get('message')}")
            _, fresh_data = fetch_week_rankings(selected_week)
            if isinstance(fresh_data, dict) and "gateways" in fresh_data:
                st.session_state.rankings_data = fresh_data.get("gateways", [])
                st.session_state.last_loaded_week = selected_week
        else:
            st.error(f"Run failed (HTTP {code}): {resp.get('detail')}")

# ---------------------------------------------------------
# Summary Metrics Row
# ---------------------------------------------------------
current_list = st.session_state.rankings_data or []
active_week_str = st.session_state.last_loaded_week or selected_week
top_score = f"{current_list[0]['score']:.1f} hrs" if current_list else "—"

m_col1, m_col2, m_col3, m_col4 = st.columns(4)

with m_col1:
    st.metric(
        label="Visit Quota",
        value=f"{len(current_list)} / 15",
        delta="100% capacity scheduled" if len(current_list) == 15 else None,
    )

with m_col2:
    st.metric(
        label="Selected Week",
        value=active_week_str,
        delta="Trailing 28d baseline",
        delta_color="off",
    )

with m_col3:
    st.metric(
        label="Max Anomaly Score",
        value=top_score,
        delta="Worst deviation (#1)",
        delta_color="inverse",
    )

with m_col4:
    st.metric(
        label="FastAPI Backend",
        value="Port 8000",
        delta="Connected" if is_online else "Offline",
        delta_color="normal" if is_online else "inverse",
    )

st.divider()

# ---------------------------------------------------------
# Tabbed Views
# ---------------------------------------------------------
tab_table, tab_diag, tab_info = st.tabs([
    "📋 Weekly Visit Schedule (Top 15)",
    "🔍 Gateway Diagnostic Audit",
    "🏗️ System Architecture & API",
])

# ---------------------------------------------------------
# TAB 1: Table View
# ---------------------------------------------------------
with tab_table:
    if current_list:
        df = pd.DataFrame(current_list)

        table_df = pd.DataFrame({
            "Rank": df["rank"].astype(int),
            "Gateway ID": df["gateway_id"].astype(str),
            "Anomaly Score (Breach Hours)": df["score"].astype(float),
            "Diagnostic Audit Reason": df["reason"].astype(str),
        })

        st.subheader(f"Prioritized Gateways for Week {active_week_str}")
        st.caption("Sorted descending by total 3-sigma breach hours in trailing 7 days. Maximum 15 field visits allocated.")

        st.dataframe(
            table_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Rank": st.column_config.NumberColumn("Rank", format="#%d", width="small"),
                "Gateway ID": st.column_config.TextColumn("Gateway ID", width="medium"),
                "Anomaly Score (Breach Hours)": st.column_config.ProgressColumn(
                    "Anomaly Score (Breach Hours)",
                    format="%.1f hrs",
                    min_value=0.0,
                    max_value=50.0,
                    width="medium",
                ),
                "Diagnostic Audit Reason": st.column_config.TextColumn("Diagnostic Audit Reason", width="large"),
            },
        )

        st.write("")
        csv_data = pd.DataFrame(current_list).to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Export This Week's Visit Schedule (CSV)",
            data=csv_data,
            file_name=f"visit_schedule_{active_week_str}.csv",
            mime="text/csv",
        )
    else:
        if is_online:
            st.info("Click 'Load Rankings' above to display the weekly gateway recommendations.")

# ---------------------------------------------------------
# TAB 2: Gateway Explanation
# ---------------------------------------------------------
with tab_diag:
    st.subheader("Gateway Diagnostic Deep-Dive")
    st.caption("Inspect why a specific gateway breached statistical thresholds, or audit any gateway across the wider network.")

    exp_col1, exp_col2 = st.columns([1.6, 2.4])

    available_ids = [gw["gateway_id"] for gw in current_list] if current_list else ["0A2778A31BE3"]

    with exp_col1:
        id_mode = st.radio(
            "Select lookup method:",
            options=["From this week's top 15", "Enter custom Gateway ID"],
            horizontal=False,
        )

        if id_mode == "From this week's top 15" and available_ids:
            target_gw = st.selectbox("Select Gateway ID:", options=available_ids)
        else:
            target_gw = st.text_input("Enter Gateway ID (e.g. 0A2778A31BE3):", value=available_ids[0])

        explain_btn = st.button("🔍 Run Diagnostic Audit", use_container_width=True)

    with exp_col2:
        if explain_btn or target_gw:
            cleaned_id = target_gw.strip().upper()
            code, exp_data = fetch_gateway_explanation(cleaned_id, active_week_str)

            if code == 200:
                in_top = exp_data.get("in_top_15", False)
                rank_display = f"#{exp_data.get('rank')}" if exp_data.get("rank") is not None else "Unranked"
                score_val = f"{exp_data.get('score')} hrs" if exp_data.get("score") is not None else "0.0 hrs"

                if in_top:
                    st.success(f"✅ **Priority Site Visit Recommended (Rank {rank_display})**")
                else:
                    st.info(f"ℹ️ **Normal Operation • Outside Top 15 (No Site Visit Required)**")

                stat1, stat2, stat3 = st.columns(3)
                with stat1:
                    st.metric("Assigned Rank", rank_display)
                with stat2:
                    st.metric("3-Sigma Breach Hours", score_val)
                with stat3:
                    st.metric("Dispatch Cost", "£380" if in_top else "£0 (Saved)")

                st.markdown(f"**Diagnostic Rationale:**")
                st.info(exp_data.get("reason", "No detailed reason provided."))

            elif code == 404:
                st.error(f"Gateway Not Found (HTTP 404): {exp_data.get('detail')}")
            elif code == 400:
                st.error(f"Bad Request (HTTP 400): {exp_data.get('detail')}")
            else:
                st.error(f"Error (HTTP {code}): {exp_data.get('detail')}")

# ---------------------------------------------------------
# TAB 3: System Architecture
# ---------------------------------------------------------
with tab_info:
    st.subheader("Decoupled System Architecture")
    st.caption("Clean separation of concerns between statistical anomaly detection, REST services, and presentation.")

    info_col1, info_col2 = st.columns([1.5, 1.5])

    with info_col1:
        st.markdown(
            """
            ```
             ┌────────────────────────────────────────────────────────┐
             │       Streamlit Dashboard (Port 8501 - UI Client)      │
             └───────────────────────────┬────────────────────────────┘
                                         │ HTTP REST (httpx)
                                         ▼
             ┌────────────────────────────────────────────────────────┐
             │       FastAPI REST Service (Port 8000)                 │
             │   • GET  /health                                       │
             │   • GET  /weeks/{week_start}/rankings                  │
             │   • GET  /gateways/{gateway_id}/explanation            │
             │   • POST /run                                          │
             └───────────────────────────┬────────────────────────────┘
                                         │ Strategy Pattern
                                         ▼
             ┌────────────────────────────────────────────────────────┐
             │       RankingEngine (src/ranking/engine.py)            │
             │   • RankingStrategy Protocol                           │
             │   • ThreeSigmaStrategy (28-day baseline + 7-day test)  │
             └───────────────────────────┬────────────────────────────┘
                                         │ File I/O
                                         ▼
             ┌────────────────────────────────────────────────────────┐
             │   Telemetry Data (data/telemetry/ or predictions.csv)  │
             └────────────────────────────────────────────────────────┘
            ```
            """
        )

    with info_col2:
        st.markdown(
            """
            #### Software Engineering Highlights (Track B)
            - **No Logic Duplication:** The dashboard contains zero ranking math; all calculations are executed strictly on the FastAPI backend.
            - **Strategy Design Pattern:** New anomaly models (e.g. LightGBM, cost-weighted rankers) can be injected without altering API endpoints or UI.
            - **Fail-Safe Robustness:** Clean HTTP 400/404/422/500 error mapping with zero internal Python tracebacks exposed.
            - **Comprehensive Test Suite:** 20 automated tests covering unit logic, route integration, regression bug fixes, and end-to-end data pipelines.
            
            [Open FastAPI Swagger Documentation (http://127.0.0.1:8000/docs)](http://127.0.0.1:8000/docs)
            """
        )
