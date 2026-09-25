import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, Any
from src.analytics.utilities import analyze_utility_correlations

def render_utility_view(filtered_tickets: pd.DataFrame, tables: Dict[str, pd.DataFrame]):
    """
    Renders correlation analytics between plant utility logs (boiler, electrical) and equipment breakdowns.
    """
    st.subheader("⚡ Plant Utilities & Breakdown Correlation Engine")

    df_boiler = tables.get("daily_boiler_log", pd.DataFrame())
    df_elec = tables.get("daily_electrical_log", pd.DataFrame())

    if df_boiler.empty and df_elec.empty:
        st.info("No utility logbook data found.")
        return

    correlations = analyze_utility_correlations(df_boiler, df_elec, filtered_tickets)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🫕 Steam Boiler Feed Water Hardness & TDS Anomalies")
        blr_trend = correlations["boiler_trend"]
        if not blr_trend.empty:
            fig_blr = go.Figure()
            fig_blr.add_trace(go.Scatter(
                x=blr_trend["log_date"],
                y=blr_trend["feed_water_tds"],
                name="Feed TDS (ppm)",
                mode="lines+markers",
                line=dict(color="#38bdf8", width=2)
            ))
            fig_blr.add_trace(go.Scatter(
                x=blr_trend["log_date"],
                y=blr_trend["feed_water_hardness"],
                name="Hardness (ppm)",
                yaxis="y2",
                mode="lines+markers",
                line=dict(color="#ef4444", width=2)
            ))
            fig_blr.update_layout(
                yaxis=dict(title="TDS (ppm)", showgrid=False),
                yaxis2=dict(title="Hardness (ppm)", overlaying="y", side="right", showgrid=False),
                margin=dict(l=20, r=20, t=20, b=30),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=320,
                legend=dict(orientation="h", y=1.1)
            )
            st.plotly_chart(fig_blr, use_container_width=True)
            st.caption("ℹ️ Notice: Hardness spikes directly precede boiler safety valve scaling incidents.")

    with col2:
        st.markdown("#### ⚡ Electrical Power Quality & Voltage Swings")
        elec_trend = correlations["electrical_trend"]
        if not elec_trend.empty:
            fig_elec = go.Figure()
            fig_elec.add_trace(go.Scatter(
                x=elec_trend["log_date"],
                y=elec_trend["ht_voltage_avg"],
                name="Avg Voltage (V)",
                mode="lines+markers",
                line=dict(color="#f59e0b", width=2)
            ))
            fig_elec.add_trace(go.Scatter(
                x=elec_trend["log_date"],
                y=elec_trend["power_factor_avg"],
                name="Power Factor",
                yaxis="y2",
                mode="lines+markers",
                line=dict(color="#10b981", width=2)
            ))
            fig_elec.update_layout(
                yaxis=dict(title="Voltage (V)", showgrid=False),
                yaxis2=dict(title="Power Factor", overlaying="y", side="right", range=[0.8, 1.05], showgrid=False),
                margin=dict(l=20, r=20, t=20, b=30),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=320,
                legend=dict(orientation="h", y=1.1)
            )
            st.plotly_chart(fig_elec, use_container_width=True)
            st.caption("ℹ️ Low power factor (<0.90) and voltage spikes correlate with induction cooktop IGBT trips.")
