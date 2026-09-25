import streamlit as st
from typing import Dict, Any
from src.utils.formatting import format_minutes_to_dhm, format_hours_to_dhm

def render_kpi_cards(kpis: Dict[str, Any]):
    """
    Renders 6 executive, simplified KPI cards.
    Designed for instant comprehension by plant managers and kitchen supervisors without technical jargon.
    """
    row1_c1, row1_c2, row1_c3 = st.columns(3)
    
    # 1. Active Issues Needing Attention
    with row1_c1:
        open_count = kpis.get('open_tickets', 0)
        active_repair = kpis.get('active_repairs_count', 0)
        st.metric(
            label="🚨 Active Kitchen Issues (चालू ब्रेकडाउन)",
            value=f"{open_count} Pending",
            delta=f"{active_repair} currently in repair" if active_repair > 0 else ("All machines running" if open_count == 0 else "Waiting for tech"),
            delta_color="inverse" if open_count > 0 else "normal"
        )

    # 2. Resolved & Verified Machines
    with row1_c2:
        total = kpis.get('total_tickets', 1)
        closed_count = kpis.get('closed_tickets', 0)
        res_rate = round(closed_count / total * 100, 1) if total > 0 else 100.0
        st.metric(
            label="✅ Fixed & Resolved (हल की गई मशीनें)",
            value=f"{closed_count} Fixed",
            delta=f"{res_rate}% Resolution Rate",
            delta_color="normal"
        )

    # 3. Average Speed to Fix (MTTR)
    with row1_c3:
        formatted_mttr = format_hours_to_dhm(kpis.get('avg_mttr_hours', 0.0))
        st.metric(
            label="⚡ Avg Time to Repair (औसत रिपेयर समय)",
            value=formatted_mttr,
            delta="From work started to fixed",
            delta_color="off"
        )

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    row2_c1, row2_c2, row2_c3 = st.columns(3)

    # 4. Technician Response Delay
    with row2_c1:
        formatted_delay = format_minutes_to_dhm(kpis.get('avg_response_delay_mins', 0.0))
        delayed_cnt = kpis.get('delayed_response_count', 0)
        st.metric(
            label="⏳ Avg Start Delay (काम शुरू होने में देरी)",
            value=formatted_delay,
            delta=f"{delayed_cnt} took >30m to start" if delayed_cnt > 0 else "Prompt response",
            delta_color="inverse" if delayed_cnt > 0 else "normal"
        )

    # 5. Dual Verification Sign-off
    with row2_c2:
        ver_pct = kpis.get('dual_verified_pct', 0.0)
        st.metric(
            label="🛡️ Dual Sign-off Rate (सत्यापन दर)",
            value=f"{ver_pct}% Verified",
            delta="Signed by Kitchen In-charge & Admin",
            delta_color="normal" if ver_pct >= 50 else "off"
        )

    # 6. Spare Parts
    with row2_c3:
        spares_cnt = kpis.get('total_spares_used', 0)
        crit_spares = kpis.get('critical_spares_used', 0)
        st.metric(
            label="🔩 Spare Parts Used (इस्तेमाल स्पेयर पार्ट्स)",
            value=f"{spares_cnt} Parts",
            delta=f"{crit_spares} critical components" if crit_spares > 0 else "Normal consumables",
            delta_color="inverse" if crit_spares > 0 else "off"
        )
