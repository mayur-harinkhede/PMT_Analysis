import pandas as pd
import numpy as np
from typing import Dict, Any

def calculate_equipment_pareto(df_tickets: pd.DataFrame, df_equipments: pd.DataFrame) -> pd.DataFrame:
    """
    Computes Pareto 80/20 analysis on equipment breakdown downtime and count.
    Returns ranked DataFrame with cumulative downtime percentage.
    """
    if df_tickets.empty or df_equipments.empty:
        return pd.DataFrame()

    # Calculate downtime per ticket in hours
    t_copy = df_tickets.copy()
    t_copy["downtime_hours"] = 0.0
    
    valid_dt = t_copy["breakdown_time"].notna() & t_copy["ticket_completion_time"].notna()
    t_copy.loc[valid_dt, "downtime_hours"] = (
        pd.to_datetime(t_copy.loc[valid_dt, "ticket_completion_time"]) - 
        pd.to_datetime(t_copy.loc[valid_dt, "breakdown_time"])
    ).dt.total_seconds() / 3600.0

    # In progress / active tickets estimate
    active_dt = t_copy["breakdown_time"].notna() & t_copy["ticket_completion_time"].isna()
    t_copy.loc[active_dt, "downtime_hours"] = (
        pd.Timestamp.now() - pd.to_datetime(t_copy.loc[active_dt, "breakdown_time"])
    ).dt.total_seconds() / 3600.0

    # Aggregate by equipment
    agg = t_copy.groupby("equipment_id").agg(
        total_tickets=("id", "count"),
        total_downtime_hours=("downtime_hours", "sum"),
        last_breakdown=("breakdown_time", "max")
    ).reset_index()

    # Merge with equipment metadata
    merged = agg.merge(df_equipments, left_on="equipment_id", right_on="id", how="left")
    merged["total_downtime_hours"] = merged["total_downtime_hours"].round(1)

    # Sort descending by downtime
    merged = merged.sort_values(by="total_downtime_hours", ascending=False).reset_index(drop=True)

    # Compute Cumulative Percentage for Pareto
    total_dt_sum = merged["total_downtime_hours"].sum()
    if total_dt_sum > 0:
        merged["cum_downtime_pct"] = (merged["total_downtime_hours"].cumsum() / total_dt_sum * 100).round(1)
    else:
        merged["cum_downtime_pct"] = 0.0

    # Estimate MTBF (Assuming 720 operating hours per month)
    operating_hours = 720.0
    merged["calculated_mtbf_hours"] = (
        (operating_hours - merged["total_downtime_hours"]) / merged["total_tickets"]
    ).apply(lambda x: round(max(x, 10.0), 1))

    return merged

def calculate_category_breakdown(df_tickets: pd.DataFrame) -> pd.DataFrame:
    """Computes breakdown count and percentage by failure category."""
    if df_tickets.empty:
        return pd.DataFrame()

    counts = df_tickets["category"].value_counts().reset_index()
    counts.columns = ["category", "ticket_count"]
    total = counts["ticket_count"].sum()
    counts["percentage"] = (counts["ticket_count"] / total * 100).round(1)
    return counts
