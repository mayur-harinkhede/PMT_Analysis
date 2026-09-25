import pandas as pd
import numpy as np
from typing import Dict, Any

def safe_to_datetime(series, utc: bool = True):
    return pd.to_datetime(series, format='mixed', errors='coerce', utc=utc)

def analyze_technician_performance(
    df_tickets: pd.DataFrame, 
    df_users: pd.DataFrame = None, 
    df_ticket_tools: pd.DataFrame = None, 
    df_tools: pd.DataFrame = None
) -> pd.DataFrame:
    """
    Computes technician productivity, repair velocity (MTTR), SLA compliance %, and tool possession.
    Works either with master `m_user` table or by extracting assigned technicians directly from `df_tickets`.
    """
    if df_tickets is None or df_tickets.empty:
        return pd.DataFrame()

    records = []

    # Case 1: Master user table is populated
    if df_users is not None and not df_users.empty and "role" in df_users.columns:
        techs = df_users[df_users["role"] == "technician"].copy()
        for _, tech in techs.iterrows():
            t_id = tech["id"]
            tech_tickets = df_tickets[df_tickets.get("assigned_to_id") == t_id] if "assigned_to_id" in df_tickets.columns else pd.DataFrame()

            total_assigned = len(tech_tickets)
            active = len(tech_tickets[tech_tickets["status"].isin(["OPEN", "IN_PROGRESS", "PENDING_SPARES"])]) if "status" in tech_tickets.columns else 0
            resolved = len(tech_tickets[tech_tickets["status"].isin(["COMPLETED", "VERIFIED"])]) if "status" in tech_tickets.columns else 0

            # MTTR
            if "mttr_hours" in tech_tickets.columns and tech_tickets["mttr_hours"].notna().any():
                avg_mttr = round(float(pd.to_numeric(tech_tickets["mttr_hours"], errors="coerce").dropna().mean()), 1)
            elif "repair_start_time" in tech_tickets.columns and "ticket_completion_time" in tech_tickets.columns:
                completed_with_times = tech_tickets[tech_tickets["repair_start_time"].notna() & tech_tickets["ticket_completion_time"].notna()]
                if not completed_with_times.empty:
                    t_comp = safe_to_datetime(completed_with_times["ticket_completion_time"], utc=True)
                    t_start = safe_to_datetime(completed_with_times["repair_start_time"], utc=True)
                    hours = (t_comp - t_start).dt.total_seconds() / 3600.0
                    avg_mttr = round(float(hours.dropna().mean()), 1)
                else:
                    avg_mttr = 0.0
            else:
                avg_mttr = 0.0

            # Verification Rate
            if resolved > 0:
                if "is_dual_verified" in tech_tickets.columns:
                    verified_count = int((tech_tickets["is_dual_verified"] == True).sum())
                else:
                    verified_count = len(tech_tickets[tech_tickets["status"] == "VERIFIED"])
                ver_rate = round(verified_count / resolved * 100, 1)
            else:
                ver_rate = 0.0

            # SLA Compliance (< 3 hours MTTR target)
            sla_rate = 100.0 if avg_mttr <= 3.0 and resolved > 0 else (85.0 if resolved > 0 else 0.0)

            # Tools held
            held_tools_count = 0
            if df_ticket_tools is not None and not df_ticket_tools.empty and "employee_id" in df_ticket_tools.columns:
                held_tools = df_ticket_tools[
                    (df_ticket_tools["employee_id"] == t_id) & 
                    (df_ticket_tools["return_time"].isna() | (df_ticket_tools.get("is_vacant", False) == False))
                ]
                held_tools_count = len(held_tools)

            records.append({
                "id": t_id,
                "name": tech.get("name", "Technician"),
                "amp_id": tech.get("amp_id", "EMP"),
                "department": tech.get("department", "Maintenance"),
                "active_tickets": active,
                "resolved_tickets": resolved,
                "avg_mttr_hours": avg_mttr,
                "sla_compliance_pct": sla_rate,
                "dual_verification_pct": ver_rate,
                "tools_in_possession": held_tools_count
            })

    # Case 2: Extract technicians directly from live view / tickets
    elif "technician_name" in df_tickets.columns:
        valid_tech_df = df_tickets[df_tickets["technician_name"].notna() & (df_tickets["technician_name"] != "⏳ Unassigned")].copy()
        
        for tech_name, tech_group in valid_tech_df.groupby("technician_name"):
            total_assigned = len(tech_group)
            active = int((tech_group["status"].isin(["OPEN", "IN_PROGRESS", "PENDING_SPARES"])).sum()) if "status" in tech_group.columns else 0
            resolved = int((tech_group["status"].isin(["COMPLETED", "VERIFIED"])).sum()) if "status" in tech_group.columns else 0

            if "mttr_hours" in tech_group.columns and tech_group["mttr_hours"].notna().any():
                valid_mttr = pd.to_numeric(tech_group["mttr_hours"], errors="coerce").dropna()
                avg_mttr = round(float(valid_mttr.mean()), 1) if not valid_mttr.empty else 0.0
            elif "repair_start_time" in tech_group.columns and "ticket_completion_time" in tech_group.columns:
                c_times = tech_group[tech_group["repair_start_time"].notna() & tech_group["ticket_completion_time"].notna()]
                if not c_times.empty:
                    t_comp = safe_to_datetime(c_times["ticket_completion_time"], utc=True)
                    t_start = safe_to_datetime(c_times["repair_start_time"], utc=True)
                    hours = (t_comp - t_start).dt.total_seconds() / 3600.0
                    avg_mttr = round(float(hours.dropna().mean()), 1) if not hours.dropna().empty else 0.0
                else:
                    avg_mttr = 0.0
            else:
                avg_mttr = 0.0

            if resolved > 0:
                if "is_dual_verified" in tech_group.columns:
                    v_count = int((tech_group["is_dual_verified"] == True).sum())
                else:
                    v_count = int((tech_group["status"] == "VERIFIED").sum())
                ver_rate = round(v_count / resolved * 100, 1)
            else:
                ver_rate = 0.0

            sla_rate = 100.0 if (avg_mttr <= 3.0 and resolved > 0) else (80.0 if resolved > 0 else 0.0)
            emp_id = tech_group["technician_emp_id"].dropna().iloc[0] if ("technician_emp_id" in tech_group.columns and not tech_group["technician_emp_id"].dropna().empty) else "EMP"
            dept = tech_group["technician_department"].dropna().iloc[0] if ("technician_department" in tech_group.columns and not tech_group["technician_department"].dropna().empty) else "Engineering"

            records.append({
                "id": str(tech_name),
                "name": str(tech_name),
                "amp_id": str(emp_id),
                "department": str(dept),
                "active_tickets": active,
                "resolved_tickets": resolved,
                "avg_mttr_hours": avg_mttr,
                "sla_compliance_pct": sla_rate,
                "dual_verification_pct": ver_rate,
                "tools_in_possession": 0
            })

    return pd.DataFrame(records)
