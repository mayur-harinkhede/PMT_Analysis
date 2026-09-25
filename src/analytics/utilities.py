import pandas as pd
from typing import Dict, Any

def safe_to_datetime(series, utc: bool = True):
    return pd.to_datetime(series, format='mixed', errors='coerce', utc=utc)

def analyze_utility_correlations(
    df_boiler_log: pd.DataFrame = None, 
    df_electrical_log: pd.DataFrame = None, 
    df_tickets: pd.DataFrame = None
) -> Dict[str, Any]:
    """
    Correlates plant utilities (Boiler TDS/Hardness & Electrical Voltage/Power Factor) with breakdown incidents.
    """
    boiler_trend = pd.DataFrame()
    electrical_trend = pd.DataFrame()

    if df_boiler_log is not None and not df_boiler_log.empty and "log_date" in df_boiler_log.columns:
        boiler_trend = df_boiler_log.sort_values(by="log_date").copy()
        boiler_trend["log_date"] = safe_to_datetime(boiler_trend["log_date"], utc=False)

    if df_electrical_log is not None and not df_electrical_log.empty and "log_date" in df_electrical_log.columns:
        electrical_trend = df_electrical_log.sort_values(by="log_date").copy()
        electrical_trend["log_date"] = safe_to_datetime(electrical_trend["log_date"], utc=False)

    boiler_breakdowns_by_date = {}
    electrical_breakdowns_by_date = {}

    if df_tickets is not None and not df_tickets.empty and "breakdown_time" in df_tickets.columns:
        t_bk = safe_to_datetime(df_tickets["breakdown_time"], utc=True)
        df_tickets_temp = df_tickets.copy()
        df_tickets_temp["event_date"] = t_bk.dt.date
        
        if "category" in df_tickets_temp.columns:
            blr_t = df_tickets_temp[df_tickets_temp["category"] == "Steam / Boiler"]
            for d, count in blr_t["event_date"].value_counts().items():
                boiler_breakdowns_by_date[str(d)] = count

            elec_t = df_tickets_temp[df_tickets_temp["category"].isin(["Electrical", "Refrigeration"])]
            for d, count in elec_t["event_date"].value_counts().items():
                electrical_breakdowns_by_date[str(d)] = count

    return {
        "boiler_trend": boiler_trend,
        "electrical_trend": electrical_trend,
        "boiler_breakdown_counts": boiler_breakdowns_by_date,
        "electrical_breakdown_counts": electrical_breakdowns_by_date
    }
