import pandas as pd
import numpy as np
from typing import Dict, Any

def safe_to_datetime(series, utc: bool = True):
    """Safely converts a series or value to datetime with mixed/ISO8601 formatting."""
    return pd.to_datetime(series, format='mixed', errors='coerce', utc=utc)

def calculate_kpis(df_tickets: pd.DataFrame, df_pm: pd.DataFrame = None, df_spares_used: pd.DataFrame = None, df_spares_meta: pd.DataFrame = None) -> Dict[str, Any]:
    """
    Computes SLA & Operational KPIs from live database tickets and view:
    - MTTR (Mean Time to Repair)
    - Response Time (Acknowledge / Dispatch Delay)
    - Total Downtime
    - PM vs CM Ratio %
    - Dual-Verification Compliance %
    - Total Spares & Critical Spares Burn Rate
    """
    if df_tickets is None or df_tickets.empty:
        return {
            "total_tickets": 0, "open_tickets": 0, "closed_tickets": 0,
            "avg_mttr_hours": 0.0, "avg_mttr_mins": 0.0,
            "total_downtime_hours": 0.0, "avg_response_delay_mins": 0.0,
            "pm_ratio_pct": 0.0, "dual_verified_pct": 0.0,
            "total_spares_used": 0, "critical_spares_used": 0,
            "delayed_response_count": 0, "active_repairs_count": 0
        }

    total_tickets = len(df_tickets)
    
    # Status check
    if "status" in df_tickets.columns:
        open_tickets = int((~df_tickets["status"].isin(["COMPLETED", "VERIFIED"])).sum())
        closed_tickets = total_tickets - open_tickets
        active_repairs = int((df_tickets["status"] == "IN_PROGRESS").sum())
    else:
        open_tickets = 0
        closed_tickets = total_tickets
        active_repairs = 0

    # 1. MTTR: pre-computed mttr_hours / mttr_mins or (ticket_completion_time - repair_start_time)
    if "mttr_mins" in df_tickets.columns and df_tickets["mttr_mins"].notna().any():
        valid_mttr = pd.to_numeric(df_tickets["mttr_mins"], errors="coerce").dropna()
        avg_mttr_mins = round(float(valid_mttr.mean()), 1) if not valid_mttr.empty else 0.0
        avg_mttr_hours = round(avg_mttr_mins / 60.0, 2)
    elif "repair_start_time" in df_tickets.columns and "ticket_completion_time" in df_tickets.columns:
        completed_with_times = df_tickets[
            df_tickets["repair_start_time"].notna() & 
            df_tickets["ticket_completion_time"].notna()
        ].copy()
        if not completed_with_times.empty:
            t_comp = safe_to_datetime(completed_with_times["ticket_completion_time"], utc=True)
            t_start = safe_to_datetime(completed_with_times["repair_start_time"], utc=True)
            repair_durations = (t_comp - t_start).dt.total_seconds() / 60.0
            repair_durations = repair_durations.dropna()
            avg_mttr_mins = round(float(repair_durations.mean()), 1) if not repair_durations.empty else 0.0
            avg_mttr_hours = round(avg_mttr_mins / 60.0, 2)
        else:
            avg_mttr_mins = 0.0
            avg_mttr_hours = 0.0
    else:
        avg_mttr_mins = 0.0
        avg_mttr_hours = 0.0

    # 2. Total Downtime: precomputed total_downtime_hours or (ticket_completion_time - breakdown_time)
    if "total_downtime_hours" in df_tickets.columns and df_tickets["total_downtime_hours"].notna().any():
        valid_dt = pd.to_numeric(df_tickets["total_downtime_hours"], errors="coerce").dropna()
        total_downtime_hours = round(float(valid_dt.sum()), 1) if not valid_dt.empty else 0.0
    elif "breakdown_time" in df_tickets.columns and "ticket_completion_time" in df_tickets.columns:
        downtime_df = df_tickets[
            df_tickets["breakdown_time"].notna() & 
            df_tickets["ticket_completion_time"].notna()
        ].copy()
        if not downtime_df.empty:
            t_comp = safe_to_datetime(downtime_df["ticket_completion_time"], utc=True)
            t_bk = safe_to_datetime(downtime_df["breakdown_time"], utc=True)
            downtimes = (t_comp - t_bk).dt.total_seconds() / 3600.0
            downtimes = downtimes.dropna()
            total_downtime_hours = round(float(downtimes.sum()), 1) if not downtimes.empty else 0.0
        else:
            total_downtime_hours = 0.0
    else:
        total_downtime_hours = 0.0

    # 3. Response Delay (Acknowledge Time)
    if "response_delay_mins" in df_tickets.columns and df_tickets["response_delay_mins"].notna().any():
        valid_resp = pd.to_numeric(df_tickets["response_delay_mins"], errors="coerce").dropna()
        avg_response_delay_mins = round(float(valid_resp.mean()), 1) if not valid_resp.empty else 0.0
        delayed_count = int((valid_resp > 30.0).sum())
    elif "ticket_raised_time" in df_tickets.columns and "repair_start_time" in df_tickets.columns:
        resp_df = df_tickets[
            df_tickets["ticket_raised_time"].notna() & 
            df_tickets["repair_start_time"].notna()
        ].copy()
        if not resp_df.empty:
            t_start = safe_to_datetime(resp_df["repair_start_time"], utc=True)
            t_raised = safe_to_datetime(resp_df["ticket_raised_time"], utc=True)
            resp_mins = (t_start - t_raised).dt.total_seconds() / 60.0
            resp_mins = resp_mins.dropna()
            avg_response_delay_mins = round(float(resp_mins.mean()), 1) if not resp_mins.empty else 0.0
            delayed_count = int((resp_mins > 30.0).sum())
        else:
            avg_response_delay_mins = 0.0
            delayed_count = 0
    else:
        avg_response_delay_mins = 0.0
        delayed_count = 0

    # 4. PM Ratio: (Planned PM Tasks / (Planned PM Tasks + Breakdown Tickets))
    total_pm_achieved = 0
    if df_pm is not None and not df_pm.empty and "is_achieved" in df_pm.columns:
        total_pm_achieved = int((df_pm["is_achieved"] == True).sum())
    total_events = total_pm_achieved + total_tickets
    pm_ratio_pct = round((total_pm_achieved / total_events * 100), 1) if total_events > 0 else 0.0

    # 5. Dual Verification Compliance: (admin_verified == True and raiser_verified == True)
    if total_tickets > 0:
        if "is_dual_verified" in df_tickets.columns:
            dual_verified_count = int((df_tickets["is_dual_verified"] == True).sum())
        elif "is_admin_verified" in df_tickets.columns and "is_raiser_verified" in df_tickets.columns:
            dual_verified_count = int(((df_tickets["is_admin_verified"] == True) & (df_tickets["is_raiser_verified"] == True)).sum())
        elif "admin_verified" in df_tickets.columns and "raiser_verified" in df_tickets.columns:
            dual_verified_count = int(((df_tickets["admin_verified"] == True) & (df_tickets["raiser_verified"] == True)).sum())
        else:
            dual_verified_count = 0
        dual_verified_pct = round((dual_verified_count / total_tickets * 100), 1)
    else:
        dual_verified_pct = 0.0

    # 6. Spares Count (Unpack from JSON or relational tables)
    total_spares_used = 0
    critical_spares_used = 0
    if "total_spares_used_count" in df_tickets.columns and df_tickets["total_spares_used_count"].notna().any():
        total_spares_used = int(pd.to_numeric(df_tickets["total_spares_used_count"], errors="coerce").fillna(0).sum())
    
    # Check spares_json inside df_tickets if present
    if "spares_json" in df_tickets.columns:
        import json
        for val in df_tickets["spares_json"].dropna():
            if isinstance(val, str):
                try:
                    val = json.loads(val)
                except Exception:
                    val = []
            if isinstance(val, list):
                for item in val:
                    if isinstance(item, dict):
                        qty = int(item.get("used_qty", 1) or 1)
                        if total_spares_used == 0:
                            total_spares_used += qty
                        if item.get("is_critical") is True:
                            critical_spares_used += qty

    if total_spares_used == 0 and df_spares_used is not None and not df_spares_used.empty and "used_qty" in df_spares_used.columns:
        filtered_ticket_ids = df_tickets["id"].tolist() if "id" in df_tickets.columns else []
        relevant_spares = df_spares_used[df_spares_used["ticket_id"].isin(filtered_ticket_ids)] if filtered_ticket_ids else df_spares_used
        total_spares_used = int(relevant_spares["used_qty"].sum()) if not relevant_spares.empty else 0

        if df_spares_meta is not None and not df_spares_meta.empty and "is_critical" in df_spares_meta.columns and not relevant_spares.empty:
            merged_spares = relevant_spares.merge(df_spares_meta, left_on="spare_id", right_on="id", how="inner")
            if "is_critical" in merged_spares.columns and "used_qty" in merged_spares.columns:
                critical_spares_used = int(merged_spares[merged_spares["is_critical"] == True]["used_qty"].sum())

    return {
        "total_tickets": total_tickets,
        "open_tickets": open_tickets,
        "closed_tickets": closed_tickets,
        "active_repairs_count": active_repairs,
        "avg_mttr_hours": avg_mttr_hours,
        "avg_mttr_mins": avg_mttr_mins,
        "total_downtime_hours": total_downtime_hours,
        "avg_response_delay_mins": avg_response_delay_mins,
        "delayed_response_count": delayed_count,
        "pm_ratio_pct": pm_ratio_pct,
        "dual_verified_pct": dual_verified_pct,
        "total_spares_used": total_spares_used,
        "critical_spares_used": critical_spares_used
    }
