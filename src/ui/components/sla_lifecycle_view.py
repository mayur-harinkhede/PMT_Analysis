import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any
from src.analytics.sla_lifecycle import analyze_status_lifecycle_and_bottlenecks
from src.utils.formatting import format_minutes_to_dhm, format_hours_to_dhm

def render_sla_lifecycle_view(filtered_tickets: pd.DataFrame, tables: Dict[str, pd.DataFrame]):
    """
    Renders Section 1: Core Performance & SLA Metrics (Time & Efficiency)
    - MTTR Breakdown
    - Response & Dispatch Acknowledge Time
    - Total Machine Downtime
    - Status Lifecycle & Bottleneck Duration (ticket_status_history)
    - Verification Latency (formatted in Days / Hours / Minutes)
    """
    st.subheader("⏱️ SLA Performance, Status Lifecycle & Bottlenecks")

    df_status_history = tables.get("ticket_status_history", pd.DataFrame())
    if filtered_tickets.empty:
        st.info("No tickets available for SLA lifecycle analysis.")
        return

    lifecycle = analyze_status_lifecycle_and_bottlenecks(df_status_history, filtered_tickets)
    stage_durations = lifecycle["stage_durations"]
    ver_df = lifecycle["verification_latency_df"]

    # Format delays to Days, Hours, and Minutes
    formatted_raiser_delay = format_minutes_to_dhm(lifecycle.get('avg_raiser_ver_delay_mins', 0.0))
    formatted_admin_delay = format_minutes_to_dhm(lifecycle.get('avg_admin_ver_delay_mins', 0.0))

    # Top Metric Callouts
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(
            label="Avg Raiser Sign-off Delay",
            value=formatted_raiser_delay,
            delta="After completion"
        )
    with c2:
        st.metric(
            label="Avg Admin Verification Delay",
            value=formatted_admin_delay,
            delta="After completion",
            delta_color="inverse" if (lifecycle.get('avg_admin_ver_delay_mins') or 0) > 60 else "normal"
        )
    with c3:
        # Longest bottleneck stage
        if not stage_durations.empty:
            longest_stage = stage_durations.sort_values(by="avg_duration_mins", ascending=False).iloc[0]
            longest_dur_str = format_minutes_to_dhm(longest_stage.get('avg_duration_mins', 0.0))
            st.metric(
                label="Longest Lifecycle Stage",
                value=f"{longest_stage['to_status']}",
                delta=f"Avg {longest_dur_str} per ticket",
                delta_color="inverse"
            )
        else:
            st.metric(
                label="Longest Lifecycle Stage",
                value="N/A",
                delta="No transition bottlenecks"
            )

    st.markdown("---")

    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown("#### ⏳ Status Lifecycle Bottlenecks: Average Duration per Stage")
        if not stage_durations.empty:
            fig = px.bar(
                stage_durations,
                x="to_status",
                y="avg_duration_hours",
                color="avg_duration_hours",
                color_continuous_scale="Reds",
                labels={"avg_duration_hours": "Average Duration (Hours)", "to_status": "Lifecycle Stage"},
                text="avg_duration_hours"
            )
            fig.update_layout(
                margin=dict(l=20, r=20, t=20, b=30),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=320
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### 🛡️ Verification Latency Distribution (Minutes)")
        if not ver_df.empty and ver_df["admin_ver_delay_mins"].notna().any():
            fig_ver = go.Figure()
            fig_ver.add_trace(go.Box(
                y=ver_df["raiser_ver_delay_mins"].dropna(),
                name="Raiser Sign-off",
                marker_color="#38bdf8"
            ))
            fig_ver.add_trace(go.Box(
                y=ver_df["admin_ver_delay_mins"].dropna(),
                name="Admin Sign-off",
                marker_color="#c084fc"
            ))
            fig_ver.update_layout(
                yaxis=dict(title="Delay (Minutes)"),
                margin=dict(l=20, r=20, t=20, b=30),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=320
            )
            st.plotly_chart(fig_ver, use_container_width=True)

    st.markdown("#### 📋 Verification Delay Detail Log (Days / Hours / Mins)")
    if not ver_df.empty:
        display_ver = ver_df.copy()
        display_ver["formatted_raiser_delay"] = display_ver["raiser_ver_delay_mins"].apply(format_minutes_to_dhm)
        display_ver["formatted_admin_delay"] = display_ver["admin_ver_delay_mins"].apply(format_minutes_to_dhm)

        st.dataframe(
            display_ver[["ticket_no", "title", "status", "formatted_raiser_delay", "formatted_admin_delay"]].rename(columns={
                "ticket_no": "Ticket #",
                "title": "Issue Title",
                "status": "Status",
                "formatted_raiser_delay": "Raiser Sign-off Delay (d/h/m)",
                "formatted_admin_delay": "Admin Sign-off Delay (d/h/m)"
            }),
            use_container_width=True,
            hide_index=True
        )
