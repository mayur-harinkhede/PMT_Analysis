import pandas as pd
import numpy as np
from typing import Dict, Any

def safe_to_datetime(series, utc: bool = True):
    return pd.to_datetime(series, format='mixed', errors='coerce', utc=utc)

def analyze_equipment_health_and_reliability(
    df_tickets: pd.DataFrame, 
    df_equipments: pd.DataFrame = None, 
    df_pm_schedules: pd.DataFrame = None
) -> Dict[str, Any]:
    """
    Comprehensive Asset Health & Reliability Analytics:
    1. MTBF (Mean Time Between Failures)
    2. Bad Actors Pareto (Top failing assets by downtime & frequency)
    3. Root Cause & Action Taken categorization
    4. PM vs CM correlation & Overdue PM failure detection
    5. Custom / Unregistered equipment tracking
    """
    if df_tickets is None or df_tickets.empty:
        return {
            "pareto_df": pd.DataFrame(),
            "category_df": pd.DataFrame(),
            "rca_actions_df": pd.DataFrame(),
            "overdue_pm_breakdowns": pd.DataFrame(),
            "custom_equipment_df": pd.DataFrame(),
            "custom_equipment_count": 0
        }

    t_copy = df_tickets.copy()

    # 1. Custom / Unregistered Equipment Analysis
    if "custom_equipment" in t_copy.columns:
        custom_mask = t_copy["custom_equipment"].notna() & (t_copy["custom_equipment"] != "")
        custom_df = t_copy[custom_mask].copy()
        custom_count = len(custom_df)
    elif "is_custom_equipment" in t_copy.columns:
        custom_df = t_copy[t_copy["is_custom_equipment"] == True].copy()
        custom_count = len(custom_df)
    else:
        custom_df = pd.DataFrame()
        custom_count = 0

    # 2. Downtime per ticket calculation
    if "total_downtime_hours" in t_copy.columns:
        t_copy["downtime_hours"] = pd.to_numeric(t_copy["total_downtime_hours"], errors="coerce").fillna(0.0)
    elif "breakdown_time" in t_copy.columns and "ticket_completion_time" in t_copy.columns:
        t_comp = safe_to_datetime(t_copy["ticket_completion_time"], utc=True)
        t_bk = safe_to_datetime(t_copy["breakdown_time"], utc=True)
        t_copy["downtime_hours"] = (t_comp - t_bk).dt.total_seconds() / 3600.0
        t_copy["downtime_hours"] = t_copy["downtime_hours"].fillna(0.0)
    else:
        t_copy["downtime_hours"] = 0.0

    # 3. Aggregate Equipment Pareto & MTBF
    pareto_df = pd.DataFrame()
    eq_col = "equipment_name" if "equipment_name" in t_copy.columns else ("equipment_id" if "equipment_id" in t_copy.columns else None)
    
    if eq_col:
        agg = t_copy.groupby(eq_col).agg(
            breakdown_count=("id", "count") if "id" in t_copy.columns else ("ticket_no", "count"),
            total_downtime_hours=("downtime_hours", "sum"),
            last_breakdown=("breakdown_time", "max") if "breakdown_time" in t_copy.columns else (eq_col, "first")
        ).reset_index()
        
        agg["name"] = agg[eq_col].astype(str)
        agg["equipment_code"] = agg["name"].apply(lambda x: "ASSET" if x else "N/A")
        agg["model"] = "Standard"
        agg["total_downtime_hours"] = agg["total_downtime_hours"].round(1)
        agg = agg.sort_values(by="total_downtime_hours", ascending=False).reset_index(drop=True)

        total_dt_sum = agg["total_downtime_hours"].sum()
        agg["cum_downtime_pct"] = (agg["total_downtime_hours"].cumsum() / total_dt_sum * 100).round(1) if total_dt_sum > 0 else 0.0

        operating_hours_month = 720.0
        agg["mtbf_hours"] = (
            (operating_hours_month - agg["total_downtime_hours"]) / agg["breakdown_count"].clip(lower=1)
        ).apply(lambda x: round(max(x, 12.0), 1))
        
        pareto_df = agg

    # 4. Root Cause & Action Taken categorizations
    rca_cols = [c for c in ["category", "cause_of_issue", "action_taken"] if c in t_copy.columns]
    if len(rca_cols) >= 2:
        rca_actions = t_copy.groupby(rca_cols).size().reset_index(name="frequency")
        rca_actions = rca_actions.sort_values(by="frequency", ascending=False)
    else:
        rca_actions = pd.DataFrame()

    if "category" in t_copy.columns:
        cat_counts = t_copy["category"].value_counts().reset_index()
        cat_counts.columns = ["category", "ticket_count"]
        cat_counts["percentage"] = (cat_counts["ticket_count"] / len(t_copy) * 100).round(1)
    else:
        cat_counts = pd.DataFrame()

    # 5. Overdue PM Correlation
    overdue_pm_breakdowns = pd.DataFrame()
    if df_pm_schedules is not None and not df_pm_schedules.empty and "equipment_id" in t_copy.columns and "is_achieved" in df_pm_schedules.columns:
        unachieved_pm = df_pm_schedules[df_pm_schedules["is_achieved"] == False]
        if not unachieved_pm.empty:
            overdue_equip_ids = unachieved_pm["equipment_id"].unique()
            overdue_breakdown_tickets = t_copy[t_copy["equipment_id"].isin(overdue_equip_ids)]
            if not overdue_breakdown_tickets.empty:
                avail_ov = [c for c in ["ticket_no", "title", "equipment_name", "equipment_id", "breakdown_time", "cause_of_issue", "downtime_hours"] if c in overdue_breakdown_tickets.columns]
                overdue_pm_breakdowns = overdue_breakdown_tickets[avail_ov].copy()

    return {
        "pareto_df": pareto_df,
        "category_df": cat_counts,
        "rca_actions_df": rca_actions,
        "overdue_pm_breakdowns": overdue_pm_breakdowns,
        "custom_equipment_df": custom_df,
        "custom_equipment_count": custom_count
    }
