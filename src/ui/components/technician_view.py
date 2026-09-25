import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Dict, Any
from src.analytics.technicians import analyze_technician_performance
from src.utils.formatting import format_hours_to_dhm

def render_technician_view(filtered_tickets: pd.DataFrame, tables: Dict[str, pd.DataFrame]):
    """
    Renders simplified Maintenance Team Performance & Leaderboard.
    """
    st.markdown("### 👷 Kitchen Maintenance Team (मेंटेनेंस टीम लीडरबोर्ड)")
    st.caption("Track technician productivity, resolved complaints, pending workload, and repair speed.")

    df_users = tables.get("m_user", pd.DataFrame())
    df_ticket_tools = tables.get("ticket_tools", pd.DataFrame())
    df_tools = tables.get("m_tools", pd.DataFrame())

    if filtered_tickets is None or filtered_tickets.empty:
        st.info("No technician data available for the selected filter.")
        return

    tech_df = analyze_technician_performance(filtered_tickets, df_users, df_ticket_tools, df_tools)

    if tech_df.empty:
        st.info("No technicians assigned in the selected records.")
        return

    # Callouts
    top_tech = tech_df.sort_values(by="resolved_tickets", ascending=False).iloc[0]
    total_techs = len(tech_df)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(
            label="🏆 Top Fixer (सर्वाधिक रिपेयर)",
            value=f"{top_tech['name']}",
            delta=f"{top_tech['resolved_tickets']} machines fixed",
            delta_color="normal"
        )
    with c2:
        st.metric(
            label="👷 Active Technicians on Duty",
            value=f"{total_techs} Technicians",
            delta="In kitchen maintenance roster"
        )
    with c3:
        total_resolved_team = int(tech_df["resolved_tickets"].sum())
        st.metric(
            label="✅ Total Completed Jobs",
            value=f"{total_resolved_team} Fixes",
            delta="Across all kitchen facilities"
        )

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Chart & Table
    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown("##### 📊 Machines Repaired per Technician")
        fig = px.bar(
            tech_df.sort_values(by="resolved_tickets", ascending=True).tail(8),
            x="resolved_tickets",
            y="name",
            orientation="h",
            color="resolved_tickets",
            color_continuous_scale="Blues",
            labels={"resolved_tickets": "Fixed Machines", "name": "Technician"}
        )
        fig.update_layout(
            margin=dict(l=20, r=20, t=10, b=30),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=300,
            coloraxis_showscale=False
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("##### 📌 Pending Tickets by Technician")
        active_techs = tech_df[tech_df["active_tickets"] > 0]
        if not active_techs.empty:
            fig_pie = px.pie(
                active_techs,
                names="name",
                values="active_tickets",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_pie.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                height=300
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.success("✅ No pending tickets assigned to technicians currently!")

    st.markdown("##### 📋 Technician Performance Summary")
    display_tech = tech_df.copy()
    display_tech["formatted_mttr"] = display_tech["avg_mttr_hours"].apply(format_hours_to_dhm)

    st.dataframe(
        display_tech[[
            "name", "department", "resolved_tickets", "active_tickets", "formatted_mttr", "dual_verification_pct"
        ]].rename(columns={
            "name": "Technician Name",
            "department": "Department",
            "resolved_tickets": "Fixed Complaints",
            "active_tickets": "Active / Pending",
            "formatted_mttr": "Avg Time to Fix",
            "dual_verification_pct": "Sign-off Approval %"
        }),
        use_container_width=True,
        hide_index=True
    )
