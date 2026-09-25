import streamlit as st
import pandas as pd
import json
from datetime import datetime
from typing import Dict, Any
from src.utils.formatting import format_minutes_to_dhm, format_hours_to_dhm

def safe_to_datetime(series, utc: bool = True):
    return pd.to_datetime(series, format='mixed', errors='coerce', utc=utc)

def format_status_badge(status_str: str) -> str:
    s = str(status_str).upper()
    if s == "VERIFIED":
        return "🟢 Verified"
    elif s == "COMPLETED":
        return "✅ Fixed"
    elif s == "IN_PROGRESS":
        return "🟡 In Repair"
    elif s == "ASSIGNED":
        return "🟠 Assigned"
    elif s == "PENDING_SPARES":
        return "⏳ Parts Needed"
    else:
        return "⚪ Raised"

def format_priority_badge(prio_str: str) -> str:
    p = str(prio_str).upper()
    if p in ("CRITICAL", "URGENT"):
        return "🔴 Urgent"
    elif p == "HIGH":
        return "🟠 High"
    elif p == "MEDIUM":
        return "🟡 Normal"
    else:
        return "⚪ Low"

def render_ticket_explorer(filtered_tickets: pd.DataFrame, tables: Dict[str, pd.DataFrame]):
    """
    Renders simplified, user-friendly Kitchen Breakdown Ticket Tracker.
    """
    if filtered_tickets is None or filtered_tickets.empty:
        st.info("ℹ️ No tickets found matching the selected filter criteria.")
        return

    display_df = filtered_tickets.copy()

    # Pre-computed field helpers with safe fallbacks
    if "equipment_name" not in display_df.columns:
        display_df["equipment_name"] = "Asset"
    if "kitchen_name" not in display_df.columns:
        display_df["kitchen_name"] = "Kitchen"
    if "technician_name" not in display_df.columns:
        display_df["technician_name"] = "⏳ Unassigned"

    # Format Timestamps safely
    if "ticket_raised_time" in display_df.columns:
        raised_dt = safe_to_datetime(display_df["ticket_raised_time"], utc=True)
        display_df["raised_time_str"] = raised_dt.dt.strftime('%d %b, %H:%M').fillna("—")
    else:
        display_df["raised_time_str"] = "—"

    # Format Delays and Durations as Days, Hours, and Minutes
    if "response_delay_mins" in display_df.columns:
        display_df["formatted_response_delay"] = display_df["response_delay_mins"].apply(format_minutes_to_dhm)
    else:
        display_df["formatted_response_delay"] = "—"

    if "mttr_mins" in display_df.columns:
        display_df["formatted_mttr"] = display_df["mttr_mins"].apply(format_minutes_to_dhm)
    elif "mttr_hours" in display_df.columns:
        display_df["formatted_mttr"] = display_df["mttr_hours"].apply(format_hours_to_dhm)
    else:
        display_df["formatted_mttr"] = "—"

    # Visual friendly labels
    display_df["status_display"] = display_df["status"].apply(format_status_badge)
    display_df["priority_display"] = display_df["priority"].apply(format_priority_badge)

    # Action Taken clean display
    if "action_taken" not in display_df.columns:
        display_df["action_taken"] = "Work in progress"
    display_df["action_taken"] = display_df["action_taken"].fillna("Under diagnostics")

    # Table Top Bar
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.markdown(f"#### 📋 Kitchen Breakdown Logs ({len(display_df)} Issues)")
        st.caption("Live equipment breakdown complaints, assigned technicians, repair speed & sign-offs")
    with col_t2:
        csv_data = display_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Excel/CSV",
            data=csv_data,
            file_name="kitchen_breakdowns.csv",
            mime="text/csv",
            use_container_width=True
        )

    # Main Clean Table
    table_columns = [
        "ticket_no", 
        "kitchen_name",
        "equipment_name",
        "title", 
        "status_display", 
        "priority_display",
        "technician_name",
        "formatted_mttr", 
        "formatted_response_delay", 
        "action_taken"
    ]
    avail_cols = [c for c in table_columns if c in display_df.columns]

    st.dataframe(
        display_df[avail_cols].rename(columns={
            "ticket_no": "Ticket #",
            "kitchen_name": "Kitchen",
            "equipment_name": "Machine / Asset",
            "title": "Problem Reported",
            "status_display": "Status",
            "priority_display": "Urgency",
            "technician_name": "Assigned Technician",
            "formatted_mttr": "Time to Fix (MTTR)",
            "formatted_response_delay": "Start Delay",
            "action_taken": "Action Taken"
        }),
        use_container_width=True,
        hide_index=True
    )

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # Simplified Ticket Detail Viewer
    st.markdown("#### 🔍 View Single Ticket Details (विस्तृत विवरण)")
    ticket_list = [t for t in display_df["ticket_no"].dropna().tolist() if str(t).strip()]
    if ticket_list:
        selected_ticket_no = st.selectbox(
            "Select Ticket to Inspect:", 
            ticket_list,
            label_visibility="collapsed"
        )

        if selected_ticket_no:
            t = display_df[display_df["ticket_no"] == selected_ticket_no].iloc[0]

            resp_delay_str = format_minutes_to_dhm(t.get('response_delay_mins'))
            mttr_str = format_minutes_to_dhm(t.get('mttr_mins')) if pd.notna(t.get('mttr_mins')) else format_hours_to_dhm(t.get('mttr_hours'))
            downtime_str = format_hours_to_dhm(t.get('total_downtime_hours'))

            is_raiser_signed = "✅ Yes" if (t.get("is_raiser_verified") or t.get("raiser_verified")) else "⏳ Pending"
            is_admin_signed = "✅ Yes" if (t.get("is_admin_verified") or t.get("admin_verified")) else "⏳ Pending"

            st.markdown(f"""
            <div class="ticket-detail-box">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1px solid rgba(128,128,128,0.2); padding-bottom: 12px; margin-bottom: 15px;">
                    <div>
                        <span style="font-family: monospace; font-size: 1.15rem; font-weight: 800; color: #f97316;">{t.get('ticket_no', 'N/A')}</span>
                        <h3 style="margin: 4px 0 6px 0; font-size: 1.3rem;">{t.get('title', 'N/A')}</h3>
                        <span style="opacity: 0.85; font-size: 0.9rem;">
                            🏢 Kitchen: <strong>{t.get('kitchen_name', 'N/A')}</strong> | 
                            ⚙️ Machine: <strong>{t.get('equipment_name', 'N/A')}</strong>
                        </span>
                    </div>
                    <div style="text-align: right;">
                        <span class="pill pill-info">{t.get('priority', 'NORMAL')}</span>
                        <span class="pill pill-resolved">{t.get('status', 'OPEN')}</span>
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px;">
                    <div>
                        <h5 style="color: #3b82f6; margin-bottom: 8px;">🛠️ What Happened & Action Taken</h5>
                        <p style="font-size: 0.9rem; background: rgba(245,158,11,0.08); padding: 10px 14px; border-radius: 8px; border-left: 4px solid #f59e0b; margin-bottom: 10px;">
                            <strong>Cause of Issue:</strong> {t.get('cause_of_issue', 'Under diagnostics')}
                        </p>
                        <p style="font-size: 0.9rem; background: rgba(16,185,129,0.08); padding: 10px 14px; border-radius: 8px; border-left: 4px solid #10b981; margin-bottom: 10px;">
                            <strong>Action Taken:</strong> {t.get('action_taken', 'Work in progress')}
                        </p>
                        <p style="font-size: 0.88rem; opacity: 0.85;">
                            <strong>Reported By:</strong> {t.get('raised_by_name', 'Kitchen Staff')} &nbsp;|&nbsp; 
                            <strong>Technician:</strong> {t.get('technician_name', '⏳ Unassigned')}
                        </p>
                    </div>
                    
                    <div>
                        <h5 style="color: #a855f7; margin-bottom: 8px;">⏱️ Timeline & Sign-offs</h5>
                        <ul style="font-size: 0.88rem; list-style-type: none; padding-left: 0; line-height: 2;">
                            <li>📩 <strong>Complaint Raised:</strong> {t.get('ticket_raised_time', 'N/A')}</li>
                            <li>⚡ <strong>Work Started:</strong> {t.get('repair_start_time', '⏳ Pending')} (Delay: <strong>{resp_delay_str}</strong>)</li>
                            <li>🏁 <strong>Work Finished:</strong> {t.get('ticket_completion_time', '🔧 In Progress')} (Repair Time: <strong>{mttr_str}</strong>)</li>
                            <li>🛑 <strong>Total Machine Outage:</strong> <strong>{downtime_str}</strong></li>
                            <li>🛡️ <strong>Kitchen In-Charge Signed:</strong> {is_raiser_signed} &nbsp;|&nbsp; <strong>Admin Signed:</strong> {is_admin_signed}</li>
                        </ul>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Sub-arrays for parts, tools, photos
            tab_sp, tab_tl, tab_ph = st.tabs(["📦 Spare Parts Used", "🔧 Tools Used", "📷 Photo Proofs"])

            with tab_sp:
                spares_data = t.get("spares_json", [])
                if isinstance(spares_data, str):
                    try:
                        spares_data = json.loads(spares_data)
                    except Exception:
                        spares_data = []
                if spares_data and len(spares_data) > 0:
                    st.table(pd.DataFrame(spares_data))
                else:
                    st.info("No spare parts replaced for this complaint.")

            with tab_tl:
                tools_data = t.get("tools_json", [])
                if isinstance(tools_data, str):
                    try:
                        tools_data = json.loads(tools_data)
                    except Exception:
                        tools_data = []
                if tools_data and len(tools_data) > 0:
                    st.table(pd.DataFrame(tools_data))
                else:
                    st.info("No special tools issued for this repair.")

            with tab_ph:
                media_data = t.get("media_json", [])
                if isinstance(media_data, str):
                    try:
                        media_data = json.loads(media_data)
                    except Exception:
                        media_data = []
                if media_data and len(media_data) > 0:
                    cols = st.columns(len(media_data))
                    for idx, med in enumerate(media_data):
                        with cols[idx]:
                            st.caption(f"Stage: {med.get('upload_stage', 'Photo Proof')}")
                            if med.get("media_url"):
                                st.image(med["media_url"], use_container_width=True)
                else:
                    st.info("No photos uploaded for this ticket.")
