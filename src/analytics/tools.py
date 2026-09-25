import pandas as pd
import numpy as np
import json
from typing import Dict, Any

def safe_to_datetime(series, utc: bool = True):
    return pd.to_datetime(series, format='mixed', errors='coerce', utc=utc)

def analyze_tools_utilization(
    df_ticket_tools: pd.DataFrame = None, 
    df_tools: pd.DataFrame = None, 
    df_users: pd.DataFrame = None,
    df_tickets: pd.DataFrame = None
) -> Dict[str, Any]:
    """
    Analyzes Tool Utilization & Holding Times:
    1. Tool Holding Duration = return_time - taken_time
    2. Detects tool hoarding, overdue unreturned tools (is_vacant = false).
    """
    # Case 1: Relational ticket_tools & m_tools populated
    if df_ticket_tools is not None and not df_ticket_tools.empty and df_tools is not None and not df_tools.empty:
        merged = df_ticket_tools.merge(df_tools, left_on="tool_id", right_on="id", how="left")
        if df_users is not None and not df_users.empty:
            u_map = dict(zip(df_users["id"], df_users["name"]))
            merged["technician_name"] = merged["employee_id"].map(u_map).fillna("Technician")
        else:
            merged["technician_name"] = "Technician"

        merged["taken_time"] = safe_to_datetime(merged["taken_time"], utc=True)
        merged["return_time"] = safe_to_datetime(merged["return_time"], utc=True)

        returned_mask = merged["return_time"].notna()
        merged.loc[returned_mask, "holding_duration_mins"] = (
            merged.loc[returned_mask, "return_time"] - merged.loc[returned_mask, "taken_time"]
        ).dt.total_seconds() / 60.0

        held_mask = merged["return_time"].isna() & merged["taken_time"].notna()
        merged.loc[held_mask, "holding_duration_mins"] = (
            pd.Timestamp.now(tz="UTC") - merged.loc[held_mask, "taken_time"]
        ).dt.total_seconds() / 60.0

        merged["holding_duration_mins"] = merged["holding_duration_mins"].round(1)
        merged["holding_duration_hours"] = (merged["holding_duration_mins"] / 60.0).round(2)

        hoarded_mask = (merged["is_vacant"] == False) | (merged["return_time"].isna() & (merged["holding_duration_hours"] > 2.0))
        hoarded_tools = merged[hoarded_mask].copy()
        avg_holding = round(float(merged["holding_duration_mins"].dropna().mean()), 1) if not merged["holding_duration_mins"].dropna().empty else 0.0
        active_issued = len(merged[merged["is_vacant"] == False])

        return {
            "tool_history_df": merged,
            "hoarded_tools_df": hoarded_tools,
            "avg_holding_mins": avg_holding,
            "active_issued_count": active_issued
        }

    # Case 2: Unpack tools_json from live tickets
    tool_records = []
    if df_tickets is not None and not df_tickets.empty and "tools_json" in df_tickets.columns:
        for _, row in df_tickets.iterrows():
            t_raw = row.get("tools_json", [])
            if isinstance(t_raw, str):
                try:
                    t_raw = json.loads(t_raw)
                except Exception:
                    t_raw = []
            if isinstance(t_raw, list):
                for item in t_raw:
                    if isinstance(item, dict):
                        tool_records.append({
                            "tool_name": item.get("tool_name", "Maintenance Tool"),
                            "technician_name": row.get("technician_name", "Technician"),
                            "taken_time": item.get("taken_time"),
                            "return_time": item.get("return_time"),
                            "is_vacant": item.get("is_vacant", True)
                        })

    if tool_records:
        df_tl_unpacked = pd.DataFrame(tool_records)
        df_tl_unpacked["taken_time"] = safe_to_datetime(df_tl_unpacked["taken_time"], utc=True)
        df_tl_unpacked["return_time"] = safe_to_datetime(df_tl_unpacked["return_time"], utc=True)

        returned_mask = df_tl_unpacked["return_time"].notna()
        df_tl_unpacked.loc[returned_mask, "holding_duration_mins"] = (
            df_tl_unpacked.loc[returned_mask, "return_time"] - df_tl_unpacked.loc[returned_mask, "taken_time"]
        ).dt.total_seconds() / 60.0

        held_mask = df_tl_unpacked["return_time"].isna() & df_tl_unpacked["taken_time"].notna()
        df_tl_unpacked.loc[held_mask, "holding_duration_mins"] = (
            pd.Timestamp.now(tz="UTC") - df_tl_unpacked.loc[held_mask, "taken_time"]
        ).dt.total_seconds() / 60.0

        df_tl_unpacked["holding_duration_mins"] = df_tl_unpacked["holding_duration_mins"].round(1)
        df_tl_unpacked["holding_duration_hours"] = (df_tl_unpacked["holding_duration_mins"] / 60.0).round(2)

        hoarded_mask = (df_tl_unpacked["is_vacant"] == False) | (df_tl_unpacked["return_time"].isna() & (df_tl_unpacked["holding_duration_hours"] > 2.0))
        hoarded_tools = df_tl_unpacked[hoarded_mask].copy()
        avg_holding = round(float(df_tl_unpacked["holding_duration_mins"].dropna().mean()), 1) if not df_tl_unpacked["holding_duration_mins"].dropna().empty else 0.0
        active_issued = len(df_tl_unpacked[df_tl_unpacked["is_vacant"] == False])

        return {
            "tool_history_df": df_tl_unpacked,
            "hoarded_tools_df": hoarded_tools,
            "avg_holding_mins": avg_holding,
            "active_issued_count": active_issued
        }

    return {
        "tool_history_df": pd.DataFrame(),
        "hoarded_tools_df": pd.DataFrame(),
        "avg_holding_mins": 0.0,
        "active_issued_count": 0
    }
