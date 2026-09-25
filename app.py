import sys

# Flush cached submodules so Streamlit always executes the latest code without caching bugs
for mod_name in list(sys.modules.keys()):
    if mod_name.startswith("src.") or mod_name.startswith("config."):
        del sys.modules[mod_name]

import streamlit as st
import pandas as pd

from src.database.connection import db_manager
from config.settings import settings
from src.analytics.kpis import calculate_kpis
from src.ui.theme import apply_custom_theme
from src.ui.components.filters import render_filters
from src.ui.components.kpi_cards import render_kpi_cards
from src.ui.components.ticket_explorer import render_ticket_explorer
from src.ui.components.pareto_view import render_pareto_view
from src.ui.components.spares_view import render_spares_view
from src.ui.components.technician_view import render_technician_view

# Configure Streamlit Page with Indian Kitchen CMMS branding
st.set_page_config(
    page_title="Rasoi Ops — Kitchen Maintenance Hub",
    page_icon="🍲",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_live_data():
    """Live Supabase data loader."""
    try:
        if hasattr(db_manager, "fetch_live_data"):
            return db_manager.fetch_live_data()
        elif hasattr(db_manager, "get_all_tables"):
            return db_manager.get_all_tables(), "🟢 Connected to Live Supabase"
    except Exception as e:
        return {}, f"❌ Data Load Error: {e}"
    return {}, "❌ Unable to connect to Supabase"

def main():
    # Apply custom modern, uncluttered UI theme
    apply_custom_theme()

    # Load Live Tables & View directly from Supabase (Read-Only)
    tables, source_desc = load_live_data()

    # Friendly Header Banner with Indian Kitchen Context
    total_db_tickets = len(tables.get("tickets", []))
    st.markdown(f"""
    <div class="rasoi-header-banner">
        <div>
            <h1 class="rasoi-brand-title">🍲 Rasoi Ops <span style="font-size: 1.1rem; font-weight: 500; opacity: 0.7;">(रसोई ऑप्स)</span></h1>
            <p class="rasoi-brand-sub">Commercial Kitchen Equipment, Machine Breakdowns & Maintenance Hub</p>
        </div>
        <div style="text-align: right;">
            <span class="pill pill-resolved">🟢 Live Sync: {total_db_tickets} Tickets</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Handle Live Empty Database State Gracefully
    df_tickets = tables.get("tickets", pd.DataFrame())
    if df_tickets is None or df_tickets.empty:
        st.info("🟢 **Live Database Connected:** Connection is active. There are currently **0 breakdown complaints** logged. When complaints are raised, they will appear here automatically.")
        return

    # Render Sidebar Multi-Level Filters (with auto-reset on change)
    filtered_tickets = render_filters(tables)

    # Calculate High-Level Operational KPIs
    df_pm = tables.get("rep_preventive_machine_schedule", pd.DataFrame())
    df_spares_used = tables.get("spare_ticket", pd.DataFrame())
    df_spares_meta = tables.get("m_spares", pd.DataFrame())

    kpis = calculate_kpis(filtered_tickets, df_pm, df_spares_used, df_spares_meta)

    # Render Clean 6-Card Executive Summary
    render_kpi_cards(kpis)

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # Streamlined 4 Main Tabs (Simple, uncluttered navigation)
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Kitchen Breakdown Logs (शिकायतें & टिकट्स)",
        "🏭 Machine Health & Problem Assets (मशीन स्वास्थ्य)",
        "👷 Maintenance Team (मेंटेनेंस टीम)",
        "📦 Spare Parts & Utilities (स्पेयर पार्ट्स & यूटिलिटी)"
    ])

    # Tab 1: Live Shift Breakdown Complaints
    with tab1:
        render_ticket_explorer(filtered_tickets, tables)

    # Tab 2: Machine Health, Frequency & Pareto
    with tab2:
        render_pareto_view(filtered_tickets, tables)

    # Tab 3: Technician Performance & Workload
    with tab3:
        render_technician_view(filtered_tickets, tables)

    # Tab 4: Spare Parts, Tools & Boiler/Electrical Utilities
    with tab4:
        render_spares_view(tables)

if __name__ == "__main__":
    main()
