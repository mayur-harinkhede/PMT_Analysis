import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any
from src.analytics.equipment import analyze_equipment_health_and_reliability
from src.utils.formatting import format_hours_to_dhm

def render_pareto_view(filtered_tickets: pd.DataFrame, tables: Dict[str, pd.DataFrame]):
    """
    Renders simplified Machine Health & Top Breakdown Assets view.
    Focuses on practical kitchen questions: Which machine breaks down the most?
    """
    st.markdown("### 🏭 Kitchen Machine Health & Top Problem Assets (मशीन स्वास्थ्य)")
    st.caption("See which kitchen equipment causes the highest breakdown frequency and downtime.")

    df_equipments = tables.get("m_equipment", pd.DataFrame())
    df_pm = tables.get("rep_preventive_machine_schedule", pd.DataFrame())

    if filtered_tickets is None or filtered_tickets.empty:
        st.info("No ticket data available for machine health analysis.")
        return

    analysis = analyze_equipment_health_and_reliability(filtered_tickets, df_equipments, df_pm)
    pareto_df = analysis["pareto_df"]
    cat_df = analysis["category_df"]
    rca_actions = analysis["rca_actions_df"]

    # Top Highlights
    c1, c2, c3 = st.columns(3)
    with c1:
        if not pareto_df.empty:
            top_asset = pareto_df.iloc[0]
            st.metric(
                label="🚨 Most Failing Machine (सर्वाधिक ब्रेकडाउन)",
                value=f"{top_asset['name']}",
                delta=f"{top_asset['breakdown_count']} breakdowns recorded",
                delta_color="inverse"
            )
        else:
            st.metric(label="Most Failing Machine", value="All Good", delta="No breakdowns")

    with c2:
        st.metric(
            label="⚙️ Total Machines Monitored",
            value=f"{len(pareto_df)} Equipment",
            delta="In active kitchen registry"
        )

    with c3:
        top_cat = cat_df.iloc[0]["category"] if not cat_df.empty else "Normal"
        st.metric(
            label="⚠️ Top Operating Issue",
            value=top_cat,
            delta="Primary failure condition",
            delta_color="inverse"
        )

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Clean Charts
    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown("##### 📊 Top 7 Problem Machines by Breakdown Count")
        if not pareto_df.empty:
            top_assets = pareto_df.head(7).sort_values(by="breakdown_count", ascending=True)
            
            fig = px.bar(
                top_assets,
                x="breakdown_count",
                y="name",
                orientation="h",
                color="breakdown_count",
                color_continuous_scale="Oranges",
                labels={"breakdown_count": "Breakdown Frequency", "name": "Machine"}
            )
            fig.update_layout(
                margin=dict(l=20, r=20, t=10, b=30),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=320,
                coloraxis_showscale=False
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("##### 🎯 Machine Operating Conditions")
        if not cat_df.empty:
            fig_pie = px.pie(
                cat_df,
                names="category",
                values="ticket_count",
                hole=0.45,
                color_discrete_sequence=["#ef4444", "#f59e0b", "#10b981", "#3b82f6"]
            )
            fig_pie.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                height=320
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")

    # Equipment Register
    st.markdown("##### 📋 Complete Machine Breakdown History")
    if not pareto_df.empty:
        display_tbl = pareto_df.copy()
        display_tbl["formatted_downtime"] = display_tbl["total_downtime_hours"].apply(format_hours_to_dhm)
        display_tbl["formatted_mtbf"] = display_tbl["mtbf_hours"].apply(format_hours_to_dhm)

        st.dataframe(
            display_tbl[[
                "name", "breakdown_count", "formatted_downtime", "formatted_mtbf", "last_breakdown"
            ]].rename(columns={
                "name": "Machine Name",
                "breakdown_count": "Total Breakdowns",
                "formatted_downtime": "Cumulative Downtime (d/h/m)",
                "formatted_mtbf": "Time Between Failures (MTBF)",
                "last_breakdown": "Last Breakdown Date"
            }),
            use_container_width=True,
            hide_index=True
        )
