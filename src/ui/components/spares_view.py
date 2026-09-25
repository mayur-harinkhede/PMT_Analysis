import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any
from src.analytics.spares import analyze_spares_inventory_and_costs
from src.analytics.tools import analyze_tools_utilization
from src.analytics.utilities import analyze_utility_correlations
from src.utils.formatting import format_minutes_to_dhm, format_hours_to_dhm

def render_spares_view(tables: Dict[str, pd.DataFrame]):
    """
    Renders simplified, unified Spares & Plant Utilities view.
    """
    st.markdown("### 📦 Spare Parts, Tools & Kitchen Utilities")
    st.caption("Monitor spare parts consumed in repairs, tool custody, and boiler / electrical status.")

    df_spares = tables.get("m_spares", pd.DataFrame())
    df_spare_tracker = tables.get("spare_tracker", pd.DataFrame())
    df_spare_ticket = tables.get("spare_ticket", pd.DataFrame())
    df_tickets = tables.get("tickets", pd.DataFrame())
    df_tools = tables.get("m_tools", pd.DataFrame())
    df_ticket_tools = tables.get("ticket_tools", pd.DataFrame())
    df_users = tables.get("m_user", pd.DataFrame())
    df_boiler = tables.get("daily_boiler_log", pd.DataFrame())
    df_elec = tables.get("daily_electrical_log", pd.DataFrame())

    # Spares Analysis
    sp_analysis = analyze_spares_inventory_and_costs(df_spares, df_spare_tracker, df_spare_ticket, df_tickets)
    summary_df = sp_analysis["summary_df"]

    # Tools Analysis
    tool_analysis = analyze_tools_utilization(df_ticket_tools, df_tools, df_users, df_tickets)
    tool_history = tool_analysis["tool_history_df"]
    hoarded_tools = tool_analysis["hoarded_tools_df"]

    # Utilities Analysis
    util_analysis = analyze_utility_correlations(df_boiler, df_elec, df_tickets)

    sub_t1, sub_t2, sub_t3 = st.tabs([
        "🔩 Spare Parts Consumed", 
        "🫕 Steam Boiler & Power Quality", 
        "🔧 Special Tools Custody"
    ])

    # 1. Spare Parts
    with sub_t1:
        if not summary_df.empty:
            m1, m2 = st.columns(2)
            with m1:
                st.metric(
                    label="Total Spares Burn Cost",
                    value=f"₹{sp_analysis['total_spare_cost']:,.0f}",
                    delta="Parts replaced in machines"
                )
            with m2:
                total_parts = int(summary_df["used_qty"].sum()) if "used_qty" in summary_df.columns else 0
                st.metric(
                    label="Total Parts Consumed",
                    value=f"{total_parts} Units",
                    delta="Across kitchen maintenance"
                )

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            avail_cols = [c for c in ["spare_code", "spare_name", "spare_type", "used_qty", "uom", "unit_cost", "total_cost_consumed"] if c in summary_df.columns]
            st.dataframe(
                summary_df[avail_cols].rename(columns={
                    "spare_code": "Part Code",
                    "spare_name": "Part Description",
                    "spare_type": "Category",
                    "used_qty": "Quantity Used",
                    "uom": "Unit",
                    "unit_cost": "Unit Cost (₹)",
                    "total_cost_consumed": "Total Cost (₹)"
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("ℹ️ No spare parts replacement logged in the database.")

    # 2. Boiler & Utilities
    with sub_t2:
        blr_trend = util_analysis["boiler_trend"]
        elec_trend = util_analysis["electrical_trend"]

        if not blr_trend.empty or not elec_trend.empty:
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                st.markdown("##### 🫕 Steam Boiler Feed Water Quality")
                if not blr_trend.empty:
                    fig_blr = px.line(
                        blr_trend,
                        x="log_date",
                        y=["feed_water_tds", "feed_water_hardness"],
                        labels={"value": "PPM", "log_date": "Date", "variable": "Parameter"}
                    )
                    fig_blr.update_layout(margin=dict(l=10, r=10, t=10, b=20), height=280)
                    st.plotly_chart(fig_blr, use_container_width=True)
                else:
                    st.info("No boiler log entries recorded.")

            with col_b2:
                st.markdown("##### ⚡ Electrical Power Quality")
                if not elec_trend.empty:
                    fig_elec = px.line(
                        elec_trend,
                        x="log_date",
                        y=["ht_voltage_avg", "power_factor_avg"],
                        labels={"value": "Reading", "log_date": "Date", "variable": "Metric"}
                    )
                    fig_elec.update_layout(margin=dict(l=10, r=10, t=10, b=20), height=280)
                    st.plotly_chart(fig_elec, use_container_width=True)
                else:
                    st.info("No electrical log entries recorded.")
        else:
            st.info("ℹ️ No boiler or electrical sensor logs found in database. Routine logs will appear here.")

    # 3. Tools Custody
    with sub_t3:
        if not tool_history.empty:
            if not hoarded_tools.empty:
                st.warning(f"⚠️ {len(hoarded_tools)} tool(s) currently checked out by technicians for >2 hours.")
            display_th = tool_history.copy()
            display_th["formatted_holding"] = display_th["holding_duration_mins"].apply(format_minutes_to_dhm)
            st.dataframe(
                display_th[[
                    "tool_name", "technician_name", "taken_time", "formatted_holding", "is_vacant"
                ]].rename(columns={
                    "tool_name": "Special Tool",
                    "technician_name": "Technician in Custody",
                    "taken_time": "Checked Out At",
                    "formatted_holding": "Duration Held",
                    "is_vacant": "Returned"
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("ℹ️ No special tool checkouts recorded.")
