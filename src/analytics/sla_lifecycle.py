import pandas as pd
import numpy as np
import json
from typing import Dict, Any

def safe_to_datetime(series, utc: bool = True):
    return pd.to_datetime(series, format='mixed', errors='coerce', utc=utc)

def analyze_status_lifecycle_and_bottlenecks(df_status_history: pd.DataFrame, df_tickets: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes:
    1. Average duration spent in each state (e.g., OPEN -> IN_PROGRESS -> PENDING_SPARES -> COMPLETED -> VERIFIED).
    2. Verification latencies (admin_verified_at / raiser_verified_at - ticket_completion_time).
    """
    if df_tickets is None or df_tickets.empty:
        return {
            "stage_durations": pd.DataFrame(),
            "avg_raiser_ver_delay_mins": 0.0,
            "avg_admin_ver_delay_mins": 0.0,
            "verification_latency_df": pd.DataFrame()
        }

    t_copy = df_tickets.copy()
    
    # Check if pre-computed verification delays already exist from view
    if "raiser_ver_delay_mins" in t_copy.columns and t_copy["raiser_ver_delay_mins"].notna().any():
        valid_r = pd.to_numeric(t_copy["raiser_ver_delay_mins"], errors="coerce").dropna()
        avg_raiser_delay = round(float(valid_r.mean()), 1) if not valid_r.empty else 0.0
    elif "ticket_completion_time" in t_copy.columns and "raiser_verified_at" in t_copy.columns:
        valid_comp = t_copy["ticket_completion_time"].notna()
        valid_raiser = valid_comp & t_copy["raiser_verified_at"].notna()
        if valid_raiser.any():
            t_rver = safe_to_datetime(t_copy.loc[valid_raiser, "raiser_verified_at"], utc=True)
            t_comp = safe_to_datetime(t_copy.loc[valid_raiser, "ticket_completion_time"], utc=True)
            t_copy.loc[valid_raiser, "raiser_ver_delay_mins"] = (t_rver - t_comp).dt.total_seconds() / 60.0
            valid_r = t_copy.loc[valid_raiser, "raiser_ver_delay_mins"].dropna()
            avg_raiser_delay = round(float(valid_r.mean()), 1) if not valid_r.empty else 0.0
        else:
            t_copy["raiser_ver_delay_mins"] = np.nan
            avg_raiser_delay = 0.0
    else:
        t_copy["raiser_ver_delay_mins"] = np.nan
        avg_raiser_delay = 0.0

    if "admin_ver_delay_mins" in t_copy.columns and t_copy["admin_ver_delay_mins"].notna().any():
        valid_a = pd.to_numeric(t_copy["admin_ver_delay_mins"], errors="coerce").dropna()
        avg_admin_delay = round(float(valid_a.mean()), 1) if not valid_a.empty else 0.0
    elif "ticket_completion_time" in t_copy.columns and "admin_verified_at" in t_copy.columns:
        valid_comp = t_copy["ticket_completion_time"].notna()
        valid_admin = valid_comp & t_copy["admin_verified_at"].notna()
        if valid_admin.any():
            t_aver = safe_to_datetime(t_copy.loc[valid_admin, "admin_verified_at"], utc=True)
            t_comp = safe_to_datetime(t_copy.loc[valid_admin, "ticket_completion_time"], utc=True)
            t_copy.loc[valid_admin, "admin_ver_delay_mins"] = (t_aver - t_comp).dt.total_seconds() / 60.0
            valid_a = t_copy.loc[valid_admin, "admin_ver_delay_mins"].dropna()
            avg_admin_delay = round(float(valid_a.mean()), 1) if not valid_a.empty else 0.0
        else:
            t_copy["admin_ver_delay_mins"] = np.nan
            avg_admin_delay = 0.0
    else:
        t_copy["admin_ver_delay_mins"] = np.nan
        avg_admin_delay = 0.0

    # 2. Stage Durations from Status History (either direct table or unpacked from status_history_json)
    history_records = []
    if df_status_history is not None and not df_status_history.empty and "created_at" in df_status_history.columns:
        hist_sorted = df_status_history.sort_values(by=["ticket_id", "created_at"]).copy()
        hist_sorted["created_at"] = safe_to_datetime(hist_sorted["created_at"], utc=True)
        hist_sorted["next_created_at"] = hist_sorted.groupby("ticket_id")["created_at"].shift(-1)
        hist_sorted["duration_mins"] = (hist_sorted["next_created_at"] - hist_sorted["created_at"]).dt.total_seconds() / 60.0

        stage_agg = hist_sorted.groupby("to_status")["duration_mins"].agg(
            avg_duration_mins="mean",
            total_transitions="count"
        ).reset_index()
        stage_agg["avg_duration_mins"] = stage_agg["avg_duration_mins"].round(1)
        stage_agg["avg_duration_hours"] = (stage_agg["avg_duration_mins"] / 60.0).round(2)
    elif "status_history_json" in t_copy.columns:
        for _, row in t_copy.iterrows():
            t_id = row.get("id") or row.get("ticket_no")
            val = row.get("status_history_json", [])
            if isinstance(val, str):
                try:
                    val = json.loads(val)
                except Exception:
                    val = []
            if isinstance(val, list):
                for item in val:
                    if isinstance(item, dict):
                        history_records.append({
                            "ticket_id": t_id,
                            "to_status": item.get("to_status"),
                            "created_at": item.get("created_at")
                        })
        if history_records:
            df_hist_unpacked = pd.DataFrame(history_records)
            df_hist_unpacked["created_at"] = safe_to_datetime(df_hist_unpacked["created_at"], utc=True)
            df_hist_unpacked = df_hist_unpacked.sort_values(by=["ticket_id", "created_at"])
            df_hist_unpacked["next_created_at"] = df_hist_unpacked.groupby("ticket_id")["created_at"].shift(-1)
            df_hist_unpacked["duration_mins"] = (df_hist_unpacked["next_created_at"] - df_hist_unpacked["created_at"]).dt.total_seconds() / 60.0
            stage_agg = df_hist_unpacked.groupby("to_status")["duration_mins"].agg(
                avg_duration_mins="mean",
                total_transitions="count"
            ).reset_index()
            stage_agg["avg_duration_mins"] = stage_agg["avg_duration_mins"].round(1)
            stage_agg["avg_duration_hours"] = (stage_agg["avg_duration_mins"] / 60.0).round(2)
        else:
            stage_agg = pd.DataFrame()
    else:
        stage_agg = pd.DataFrame()

    avail_cols = [c for c in ["ticket_no", "title", "status", "raiser_ver_delay_mins", "admin_ver_delay_mins"] if c in t_copy.columns]
    ver_df = t_copy[avail_cols] if avail_cols else pd.DataFrame()

    return {
        "stage_durations": stage_agg,
        "avg_raiser_ver_delay_mins": avg_raiser_delay,
        "avg_admin_ver_delay_mins": avg_admin_delay,
        "verification_latency_df": ver_df
    }
