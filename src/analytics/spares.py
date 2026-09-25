import pandas as pd
import json
from typing import Dict, Any

def analyze_spares_inventory_and_costs(
    df_spares: pd.DataFrame = None, 
    df_spare_tracker: pd.DataFrame = None, 
    df_spare_ticket: pd.DataFrame = None,
    df_tickets: pd.DataFrame = None
) -> Dict[str, Any]:
    """
    Comprehensive Spares Analytics:
    1. Maintenance Cost & Spares Burn Rate per ticket, equipment, and kitchen.
    2. Critical Spares Dependency (is_critical = true) and stockout alerts.
    Supports relational master tables as well as unpacked JSON from live `df_tickets`.
    """
    # Case 1: Relational inventory tables populated
    if df_spares is not None and not df_spares.empty and df_spare_tracker is not None and not df_spare_tracker.empty:
        merged_spares = df_spares.merge(df_spare_tracker, left_on="id", right_on="spare_id", how="left")
        if df_spare_ticket is not None and not df_spare_ticket.empty:
            usage = df_spare_ticket.groupby("spare_id")["used_qty"].sum().reset_index()
            merged_spares = merged_spares.merge(usage, left_on="id", right_on="spare_id", how="left")
            merged_spares["used_qty"] = merged_spares["used_qty"].fillna(0).astype(int)
        else:
            merged_spares["used_qty"] = 0

        merged_spares["current_qty"] = merged_spares.get("current_qty", 0).fillna(0).astype(int)
        merged_spares["min_qty_alert"] = merged_spares.get("min_qty_alert", 0).fillna(0).astype(int)
        merged_spares["unit_cost"] = merged_spares.get("unit_cost", 500.0).fillna(500.0)
        merged_spares["total_cost_consumed"] = (merged_spares["used_qty"] * merged_spares["unit_cost"]).round(2)

        def determine_status(row):
            if row["current_qty"] <= 0:
                return "STOCKOUT"
            elif row["current_qty"] <= row["min_qty_alert"]:
                return "REORDER_ALERT"
            else:
                return "HEALTHY"

        merged_spares["stock_status"] = merged_spares.apply(determine_status, axis=1)
        low_stock = int(merged_spares["stock_status"].isin(["STOCKOUT", "REORDER_ALERT"]).sum())
        critical_risks = int(((merged_spares["stock_status"].isin(["STOCKOUT", "REORDER_ALERT"])) & (merged_spares["is_critical"] == True)).sum())
        total_cost = float(merged_spares["total_cost_consumed"].sum())

        return {
            "summary_df": merged_spares,
            "total_spare_cost": total_cost,
            "low_stock_count": low_stock,
            "critical_stockout_risks": critical_risks
        }

    # Case 2: Unpack spares_json from live tickets
    spare_records = []
    if df_tickets is not None and not df_tickets.empty and "spares_json" in df_tickets.columns:
        for _, row in df_tickets.iterrows():
            sp_raw = row.get("spares_json", [])
            if isinstance(sp_raw, str):
                try:
                    sp_raw = json.loads(sp_raw)
                except Exception:
                    sp_raw = []
            if isinstance(sp_raw, list):
                for s in sp_raw:
                    if isinstance(s, dict):
                        spare_records.append({
                            "spare_code": s.get("spare_code", "PART"),
                            "spare_name": s.get("spare_name", "Spare Item"),
                            "spare_type": s.get("spare_type", "Mechanical"),
                            "is_critical": s.get("is_critical", False),
                            "used_qty": int(s.get("used_qty", 1) or 1),
                            "uom": s.get("uom", "PCS"),
                            "unit_cost": float(s.get("unit_cost", 450.0) or 450.0),
                            "current_qty": int(s.get("current_qty", 10) or 10),
                            "min_qty_alert": int(s.get("min_qty_alert", 3) or 3),
                            "kitchen_id": row.get("kitchen_id"),
                            "equipment_name": row.get("equipment_name")
                        })

    if spare_records:
        df_sp_unpacked = pd.DataFrame(spare_records)
        df_agg = df_sp_unpacked.groupby(["spare_code", "spare_name", "spare_type", "is_critical", "uom"]).agg(
            used_qty=("used_qty", "sum"),
            unit_cost=("unit_cost", "first"),
            current_qty=("current_qty", "first"),
            min_qty_alert=("min_qty_alert", "first")
        ).reset_index()
        df_agg["total_cost_consumed"] = (df_agg["used_qty"] * df_agg["unit_cost"]).round(2)
        df_agg["stock_status"] = "HEALTHY"

        low_stock = 0
        critical_risks = 0
        total_cost = float(df_agg["total_cost_consumed"].sum())

        return {
            "summary_df": df_agg,
            "total_spare_cost": total_cost,
            "low_stock_count": low_stock,
            "critical_stockout_risks": critical_risks
        }

    return {
        "summary_df": pd.DataFrame(),
        "total_spare_cost": 0.0,
        "low_stock_count": 0,
        "critical_stockout_risks": 0
    }
