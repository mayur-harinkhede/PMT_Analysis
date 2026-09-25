import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

def safe_to_datetime(series, utc: bool = True):
    return pd.to_datetime(series, format='mixed', errors='coerce', utc=utc)

def reset_sub_filters():
    """Callback when Time Window or Kitchen facility filter changes: resets sub-filters to ALL."""
    st.session_state["filter_priority"] = "All Priorities"
    st.session_state["filter_status"] = "All Statuses"
    st.session_state["filter_category"] = "All Categories"
    st.session_state["filter_search"] = ""

def reset_all_filters():
    """Callback to reset all filters to default state."""
    st.session_state["filter_time_window"] = "All Time"
    st.session_state["filter_kitchen"] = "All Kitchens"
    st.session_state["filter_priority"] = "All Priorities"
    st.session_state["filter_status"] = "All Statuses"
    st.session_state["filter_category"] = "All Categories"
    st.session_state["filter_search"] = ""

def render_filters(tables: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Renders live multi-level sidebar filters for the production dashboard.
    - Kitchen facility filter directly filters on `kitchen_name`.
    - Automatically resets category, status, and priority to 'All' when time window or kitchen changes.
    """
    col_sb_title, col_sb_reset = st.sidebar.columns([3, 1])
    with col_sb_title:
        st.sidebar.markdown("### 🎛️ Filter Panel")
    with col_sb_reset:
        if st.sidebar.button("🔄 Reset", help="Reset all filters to default (All)", use_container_width=True):
            reset_all_filters()
            st.rerun()

    df_tickets = tables.get("tickets", pd.DataFrame())

    if df_tickets.empty:
        st.sidebar.info("Awaiting live ticket records from database.")
        return df_tickets

    # Initialize Session State Defaults
    if "filter_time_window" not in st.session_state:
        st.session_state["filter_time_window"] = "All Time"
    if "filter_kitchen" not in st.session_state:
        st.session_state["filter_kitchen"] = "All Kitchens"
    if "filter_priority" not in st.session_state:
        st.session_state["filter_priority"] = "All Priorities"
    if "filter_status" not in st.session_state:
        st.session_state["filter_status"] = "All Statuses"
    if "filter_category" not in st.session_state:
        st.session_state["filter_category"] = "All Categories"
    if "filter_search" not in st.session_state:
        st.session_state["filter_search"] = ""

    # 1. Date Range Preset
    date_options = [
        "All Time",
        "Today (Live Shift)", 
        "Yesterday", 
        "Last 7 Days", 
        "Last 30 Days"
    ]
    
    selected_date_preset = st.sidebar.radio(
        "📅 Time Window", 
        date_options, 
        key="filter_time_window",
        on_change=reset_sub_filters,
        help="Select a time preset. Changing this automatically resets Priority, Status, and Category to 'All'."
    )

    # 2. Kitchen Facility Filter (Directly populated from live tickets & master tables)
    kitchen_options = ["All Kitchens"]
    if "kitchen_name" in df_tickets.columns:
        for k_name in sorted(df_tickets["kitchen_name"].dropna().unique()):
            k_str = str(k_name).strip()
            if k_str and k_str not in kitchen_options:
                kitchen_options.append(k_str)

    if st.session_state["filter_kitchen"] not in kitchen_options:
        st.session_state["filter_kitchen"] = "All Kitchens"

    selected_kitchen = st.sidebar.selectbox(
        "🏢 Kitchen Facility", 
        kitchen_options,
        key="filter_kitchen",
        on_change=reset_sub_filters,
        help="Filter by kitchen location. Changing this automatically resets Priority, Status, and Category to 'All'."
    )
    
    # 3. Priority Filter
    priorities = ["All Priorities", "CRITICAL", "HIGH", "MEDIUM", "LOW"]
    if st.session_state["filter_priority"] not in priorities:
        st.session_state["filter_priority"] = "All Priorities"

    selected_priority = st.sidebar.selectbox(
        "⚡ Priority Level", 
        priorities,
        key="filter_priority"
    )

    # 4. Status Filter
    statuses = ["All Statuses", "OPEN", "IN_PROGRESS", "PENDING_SPARES", "COMPLETED", "VERIFIED"]
    if st.session_state["filter_status"] not in statuses:
        st.session_state["filter_status"] = "All Statuses"

    selected_status = st.sidebar.selectbox(
        "📌 Ticket Status", 
        statuses,
        key="filter_status"
    )

    # 5. Category Filter
    categories = ["All Categories"]
    if "category" in df_tickets.columns:
        valid_cats = sorted([str(c).strip() for c in df_tickets["category"].dropna().unique() if str(c).strip()])
        for c in valid_cats:
            if c not in categories:
                categories.append(c)

    if st.session_state["filter_category"] not in categories:
        st.session_state["filter_category"] = "All Categories"

    selected_category = st.sidebar.selectbox(
        "⚙️ Failure Category", 
        categories,
        key="filter_category"
    )

    # 6. Text Search Bar
    search_query = st.sidebar.text_input(
        "🔍 Search (Ticket#, Equipment, Issue)", 
        key="filter_search"
    ).strip().lower()

    # Apply Filtering Logic Step-by-Step
    filtered = df_tickets.copy()
    
    # 1. Date Filtering
    if "ticket_raised_time" in filtered.columns:
        dt_series = safe_to_datetime(filtered["ticket_raised_time"], utc=True)
        today_date = datetime.now(timezone.utc).date()
        yesterday_date = today_date - timedelta(days=1)

        if selected_date_preset == "Today (Live Shift)":
            if "is_today" in filtered.columns and filtered["is_today"].any():
                filtered = filtered[filtered["is_today"] == True]
            else:
                filtered = filtered[dt_series.dt.date == today_date]
        elif selected_date_preset == "Yesterday":
            filtered = filtered[dt_series.dt.date == yesterday_date]
        elif selected_date_preset == "Last 7 Days":
            cutoff = datetime.now(timezone.utc) - timedelta(days=7)
            filtered = filtered[dt_series >= cutoff]
        elif selected_date_preset == "Last 30 Days":
            cutoff = datetime.now(timezone.utc) - timedelta(days=30)
            filtered = filtered[dt_series >= cutoff]

    # 2. Kitchen Facility Filtering (Exact Match on kitchen_name)
    if selected_kitchen != "All Kitchens" and "kitchen_name" in filtered.columns:
        filtered = filtered[filtered["kitchen_name"].astype(str) == str(selected_kitchen)]

    # 3. Priority Filtering
    if selected_priority != "All Priorities" and "priority" in filtered.columns:
        filtered = filtered[filtered["priority"].astype(str).str.upper() == str(selected_priority).upper()]

    # 4. Status Filtering
    if selected_status != "All Statuses" and "status" in filtered.columns:
        filtered = filtered[filtered["status"].astype(str).str.upper() == str(selected_status).upper()]

    # 5. Category Filtering
    if selected_category != "All Categories" and "category" in filtered.columns:
        filtered = filtered[filtered["category"].astype(str) == str(selected_category)]

    # 6. Text Search Filtering
    if search_query:
        mask = pd.Series(False, index=filtered.index)
        for col in ["ticket_no", "title", "cause_of_issue", "custom_equipment", "action_taken", "equipment_name", "kitchen_name"]:
            if col in filtered.columns:
                mask = mask | filtered[col].astype(str).str.lower().str.contains(search_query, na=False)
        filtered = filtered[mask]

    st.sidebar.markdown(f"**Showing `{len(filtered)}` matching tickets**")
    return filtered
