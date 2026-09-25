import os
import sys
import io
import csv
import json
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from flask import Flask, render_template, jsonify, request, Response

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.database.connection import db_manager
from src.utils.formatting import format_minutes_to_dhm, format_hours_to_dhm

app = Flask(
    __name__, 
    template_folder=os.path.join(BASE_DIR, "templates"), 
    static_folder=os.path.join(BASE_DIR, "static")
)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response
    
def safe_to_datetime(val, utc=True):
    return pd.to_datetime(val, format='mixed', errors='coerce', utc=utc)

def get_initials(name):
    if not name or "Unassigned" in str(name):
        return "U"
    parts = str(name).strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    elif len(parts) == 1 and len(parts[0]) > 0:
        return parts[0][:2].upper()
    return "U"

def format_time_ago(dt):
    if dt is None or pd.isna(dt):
        return "—"
    try:
        now = datetime.now(timezone.utc)
        diff = now - dt
        secs = int(diff.total_seconds())
        if secs < 0:
            return "Just now"
        mins = secs // 60
        hours = mins // 60
        days = hours // 24
        if mins < 60:
            return f"{max(1, mins)}m ago"
        elif hours < 24:
            return f"{hours}h ago"
        elif days < 30:
            return f"{days}d ago"
        else:
            return dt.strftime("%d %b")
    except Exception:
        return "—"

import re

def clean_str(val, fallback="—"):
    if val is None or pd.isna(val):
        return fallback
    s = str(val).strip()
    if not s or s.lower() in ["nan", "none", "null", "nat", "—"]:
        return fallback
    return s

def resolve_equipment_name(eq_name, custom_eq=None, title=None, area_name=None, category=None):
    """
    Intelligently resolves equipment name so that custom / unregistered equipment
    are properly categorized rather than appearing as a generic 'Unregistered Asset'.
    """
    if eq_name and str(eq_name).strip() not in ["", "nan", "None", "—", "Unregistered Asset", "Unregistered", "null"]:
        return str(eq_name).strip()
    
    if custom_eq and str(custom_eq).strip() not in ["", "nan", "None", "—", "Unregistered Asset", "Unregistered", "null"]:
        return str(custom_eq).strip()
    
    t_lower = str(title or "").lower()
    
    if "rice washing" in t_lower:
        return "RICE WASHING MACHINE"
    if "rice steamer" in t_lower or "steamer" in t_lower:
        m = re.search(r"steamer\s*(?:no\.?|#)?\s*(\d+)", t_lower)
        return f"RICE STEAMER {m.group(1)}" if m else "RICE STEAMER"
    if "conveyor" in t_lower:
        if "chain" in t_lower:
            return "CHAIN CONVEYOR"
        return "RICE / DAL CONVEYOR"
    if "blower" in t_lower or "mbr" in t_lower or "settling tank" in t_lower or "collection tank" in t_lower:
        return "ETP PLANT / BLOWER"
    if "grind" in t_lower or "grinder" in t_lower:
        return "WET GRINDER"
    if "cauldron" in t_lower:
        m = re.search(r"(\d+)(?:st|nd|rd|th)?\s*cauldron", t_lower)
        return f"CAULDRON {m.group(1)}" if m else "CAULDRON"
    if "flame" in t_lower or "burner" in t_lower:
        return "BURNER / STOVE FLAME"
    if "lift" in t_lower:
        return "LIFT / ELEVATOR"
    if "exhaust" in t_lower or "exaust" in t_lower:
        return "EXHAUST FAN"
    if "tube light" in t_lower or "light" in t_lower or "lighting" in t_lower:
        return "LIGHTING / ELECTRICAL"
    if "water leak" in t_lower or "tap" in t_lower or "pipe" in t_lower or "ro water" in t_lower or "jet gun" in t_lower:
        return "PLUMBING & PIPELINE"
    if "strip curtain" in t_lower:
        return "STRIP CURTAINS"
    if "solar" in t_lower:
        return "SOLAR INVERTER & PANEL"
    if "shed" in t_lower or "rain water" in t_lower:
        return "CIVIL & SHED STRUCTURE"
    if "mcb" in t_lower or "charging" in t_lower:
        return "ELECTRICAL INFRASTRUCTURE"
    if "safety guard" in t_lower or "l angle" in t_lower:
        return "SAFETY GUARDS & FIXTURES"
        
    if title and len(str(title).strip()) > 3:
        clean_t = str(title).strip().replace('\n', ' ')
        if len(clean_t) <= 25:
            return clean_t
        return clean_t[:22] + "..."
        
    return str(area_name or "General Facility").strip()

def safe_json_load(val):
    if val is None:
        return []
    if isinstance(val, (list, dict)):
        return val
    if isinstance(val, str):
        try:
            return json.loads(val)
        except Exception:
            return []
    return []

def extract_assigned_time(row, hist):
    """
    Extracts the latest (most recent) assignment timestamp.
    Prioritizes tickets.assigned_to_time directly from the database table/view.
    Falls back to the latest ASSIGNED event in status_history_json.
    """
    for col in ["assigned_to_time", "assigned_time", "latest_assigned_time", "ticket_assigned_time", "assigned_at", "reassigned_at"]:
        if col in row and pd.notna(row[col]):
            val_str = str(row[col]).strip()
            if val_str and val_str not in ["", "nan", "None", "—", "NaT", "null"]:
                return val_str
    
    if isinstance(hist, list) and len(hist) > 0:
        assign_times = []
        for h in hist:
            if isinstance(h, dict):
                to_st = str(h.get("to_status", "")).upper()
                from_st = str(h.get("from_status", "")).upper()
                if "ASSIGN" in to_st or "ASSIGN" in from_st:
                    dt_val = h.get("created_at") or h.get("changed_at")
                    if dt_val and str(dt_val).strip() not in ["", "None", "null", "nan"]:
                        assign_times.append(str(dt_val))
        if assign_times:
            return sorted(assign_times)[-1]
            
    return "—"

def prepare_dashboard_payload():
    """
    Fetches live Supabase view records and structures them for the Executive Kitchen Maintenance Dashboard.
    """
    tables, status_desc = db_manager.fetch_live_data(tickets_only=True)
    df = tables.get("tickets", pd.DataFrame())

    if df.empty:
        return {
            "status_desc": status_desc,
            "summary": {
                "total": 0, "todo": 0, "wip": 0, "done": 0, "verified": 0,
                "raised": 0, "assigned": 0, "in_progress": 0,
                "avg_mttr_dhm": "0m", "avg_response_delay_dhm": "0m",
                "total_downtime_dhm": "0m", "dual_verified_pct": 0.0,
                "total_machines": 0
            },
            "charts": {
                "top_machines": [], "status_distribution": {},
                "technician_leaderboard": [], "condition_breakdown": []
            },
            "tickets": [],
            "kitchens": ["All Kitchens"],
            "zones": ["All Zones"],
            "categories": ["All Categories"],
            "priorities": ["All Priorities", "HIGH", "MEDIUM", "LOW"],
            "statuses": ["All Statuses", "RAISED", "ASSIGNED", "IN_PROGRESS", "COMPLETED", "VERIFIED"]
        }

    total_tickets = len(df)

    # Status counts
    status_series = df["status"].astype(str).str.upper()
    todo_count = int((status_series == "RAISED").sum())
    assigned_count = int((status_series == "ASSIGNED").sum())
    in_prog_count = int((status_series == "IN_PROGRESS").sum())
    wip_count = assigned_count + in_prog_count + int((status_series == "PENDING_SPARES").sum())
    done_count = int((status_series == "COMPLETED").sum())
    verified_count = int((status_series == "VERIFIED").sum())

    # MTTR & Response Delay & Downtime
    if "mttr_mins" in df.columns and df["mttr_mins"].notna().any():
        valid_mttr = pd.to_numeric(df["mttr_mins"], errors="coerce").dropna()
        avg_mttr_mins = float(valid_mttr.mean()) if not valid_mttr.empty else 0.0
    elif "mttr_hours" in df.columns and df["mttr_hours"].notna().any():
        valid_mttr_h = pd.to_numeric(df["mttr_hours"], errors="coerce").dropna()
        avg_mttr_mins = float(valid_mttr_h.mean() * 60.0) if not valid_mttr_h.empty else 0.0
    else:
        avg_mttr_mins = 0.0

    if "response_delay_mins" in df.columns and df["response_delay_mins"].notna().any():
        valid_resp = pd.to_numeric(df["response_delay_mins"], errors="coerce").dropna()
        avg_resp_mins = float(valid_resp.mean()) if not valid_resp.empty else 0.0
    else:
        avg_resp_mins = 0.0

    if "total_downtime_hours" in df.columns and df["total_downtime_hours"].notna().any():
        valid_dt = pd.to_numeric(df["total_downtime_hours"], errors="coerce").dropna()
        total_dt_hours = float(valid_dt.sum()) if not valid_dt.empty else 0.0
    else:
        total_dt_hours = 0.0

    # Dual verified %
    if "is_dual_verified" in df.columns:
        dual_ver_count = int((df["is_dual_verified"] == True).sum())
    else:
        dual_ver_count = verified_count
    dual_ver_pct = round(dual_ver_count / total_tickets * 100, 1) if total_tickets > 0 else 0.0

    # Status Distribution
    status_distribution = {
        "Verified": verified_count,
        "Completed": done_count,
        "In Repair": in_prog_count,
        "Assigned": assigned_count,
        "Raised": todo_count
    }

    # Technician Leaderboard
    tech_leaderboard = []
    if "technician_name" in df.columns:
        valid_techs = df[df["technician_name"].notna() & (df["technician_name"] != "⏳ Unassigned")]
        for tech_name, grp in valid_techs.groupby("technician_name"):
            res = int(grp["status"].astype(str).str.upper().isin(["COMPLETED", "VERIFIED"]).sum())
            pend = int((~grp["status"].astype(str).str.upper().isin(["COMPLETED", "VERIFIED"])).sum())
            tech_leaderboard.append({
                "name": str(tech_name),
                "resolved": res,
                "pending": pend,
                "total": res + pend
            })
        tech_leaderboard = sorted(tech_leaderboard, key=lambda x: x["resolved"], reverse=True)[:8]

    # Categories & Operating Conditions
    categories = ["All Categories"]
    condition_breakdown = []
    if "category" in df.columns:
        cat_counts = df["category"].dropna().value_counts()
        for c_name, c_cnt in cat_counts.items():
            c_str = str(c_name).strip()
            if c_str:
                if c_str not in categories:
                    categories.append(c_str)
                condition_breakdown.append({"category": c_str, "count": int(c_cnt)})

    # Kitchens
    kitchens = ["All Kitchens", "Kandi", "Narsingi", "Nellore", "Testing Kitchen"]
    if "kitchen_name" in df.columns:
        for k in sorted(df["kitchen_name"].dropna().unique()):
            k_str = str(k).strip()
            if k_str and k_str not in kitchens:
                kitchens.append(k_str)

    # Zones
    zones = ["All Zones"]
    if "zone_name" in df.columns:
        for z in sorted(df["zone_name"].dropna().unique()):
            z_str = str(z).strip()
            if z_str and z_str not in zones:
                zones.append(z_str)

    # Convert timestamps safely
    if "ticket_raised_time" in df.columns:
        raised_dt_series = safe_to_datetime(df["ticket_raised_time"], utc=True)
    else:
        raised_dt_series = pd.Series([None] * len(df))

    # Format Tickets Array & Resolve Custom Equipment
    tickets_list = []
    resolved_equipments = []
    
    for idx, r in df.iterrows():
        r_dt = raised_dt_series.iloc[idx] if idx < len(raised_dt_series) else None
        time_ago_str = format_time_ago(r_dt)

        # Durations
        m_mins = r.get("mttr_mins")
        m_hours = r.get("mttr_hours")
        mttr_dhm = format_minutes_to_dhm(m_mins) if pd.notna(m_mins) else format_hours_to_dhm(m_hours)
        resp_dhm = format_minutes_to_dhm(r.get("response_delay_mins"))
        downtime_dhm = format_hours_to_dhm(r.get("total_downtime_hours"))

        st_val = str(r.get("status", "RAISED")).upper()
        p_val = str(r.get("priority", "MEDIUM")).upper()

        raised_by = str(r.get("raised_by_name") or "Staff")
        assigned_to = str(r.get("technician_name") or "Unassigned")
        if assigned_to == "⏳ Unassigned":
            assigned_to = "Unassigned"

        history_data = safe_json_load(r.get("status_history_json"))
        assign_time_val = extract_assigned_time(r, history_data)

        # Resolve equipment accurately so 'Unregistered Asset' is mapped to custom_equipment or title
        raw_eq = clean_str(r.get("equipment_name"), "")
        custom_eq = clean_str(r.get("custom_equipment"), "")
        title_val = clean_str(r.get("title"), "")
        area_val = clean_str(r.get("area_name"), "")
        cat_val = clean_str(r.get("category"), "")

        resolved_eq = resolve_equipment_name(raw_eq, custom_eq, title_val, area_val, cat_val)
        resolved_equipments.append(resolved_eq)

        tickets_list.append({
            "id": clean_str(r.get("id"), ""),
            "ticket_no": clean_str(r.get("ticket_no"), "KMS-2026-0000"),
            "title": title_val or "No description",
            "priority": p_val,
            "raised_by": raised_by,
            "raised_by_initials": get_initials(raised_by),
            "assigned_to": assigned_to,
            "assigned_to_initials": get_initials(assigned_to),
            "status": st_val,
            "time_ago": time_ago_str,
            "kitchen_name": clean_str(r.get("kitchen_name"), "Kitchen"),
            "zone_name": clean_str(r.get("zone_name"), "—"),
            "area_name": area_val or "—",
            "equipment_name": resolved_eq,
            "raw_equipment_name": raw_eq,
            "custom_equipment": custom_eq,
            "equipment_code": clean_str(r.get("equipment_code"), "—"),
            "category": cat_val or "General",
            "action_taken": clean_str(r.get("action_taken"), "Under diagnostics"),
            "cause_of_issue": clean_str(r.get("cause_of_issue"), "Under diagnostics"),
            "ticket_raised_time": clean_str(r.get("ticket_raised_time"), "—"),
            "assigned_to_time": clean_str(r.get("assigned_to_time"), assign_time_val),
            "assigned_time": assign_time_val,
            "repair_start_time": clean_str(r.get("repair_start_time"), "—"),
            "ticket_completion_time": clean_str(r.get("ticket_completion_time"), "—"),
            "raiser_verified_at": clean_str(r.get("raiser_verified_at"), "—"),
            "admin_verified_at": clean_str(r.get("admin_verified_at"), "—"),
            "mttr_dhm": mttr_dhm,
            "response_delay_dhm": resp_dhm,
            "downtime_dhm": downtime_dhm,
            "is_today": bool(r.get("is_today", False)),
            "is_raiser_verified": bool(r.get("is_raiser_verified", False) or r.get("raiser_verified", False)),
            "is_admin_verified": bool(r.get("is_admin_verified", False) or r.get("admin_verified", False)),
            "is_dual_verified": bool(r.get("is_dual_verified", False) or ((r.get("is_raiser_verified", False) or r.get("raiser_verified", False)) and (r.get("is_admin_verified", False) or r.get("admin_verified", False)))),
            "spares": safe_json_load(r.get("spares_json")),
            "tools": safe_json_load(r.get("tools_json")),
            "media": safe_json_load(r.get("media_json")),
            "history": history_data
        })

    # Top Machines (Calculated on resolved equipment)
    top_machines = []
    if resolved_equipments:
        eq_counts = pd.Series(resolved_equipments).value_counts().head(8)
        for eq_name, count in eq_counts.items():
            top_machines.append({"name": str(eq_name), "count": int(count)})

    return {
        "status_desc": status_desc,
        "summary": {
            "total": total_tickets,
            "todo": todo_count,
            "wip": wip_count,
            "done": done_count,
            "verified": verified_count,
            "raised": todo_count,
            "assigned": assigned_count,
            "in_progress": in_prog_count,
            "avg_mttr_dhm": format_minutes_to_dhm(avg_mttr_mins),
            "avg_response_delay_dhm": format_minutes_to_dhm(avg_resp_mins),
            "total_downtime_dhm": format_hours_to_dhm(total_dt_hours),
            "dual_verified_pct": dual_ver_pct,
            "total_machines": len(top_machines)
        },
        "charts": {
            "top_machines": top_machines,
            "status_distribution": status_distribution,
            "technician_leaderboard": tech_leaderboard,
            "condition_breakdown": condition_breakdown
        },
        "tickets": tickets_list,
        "kitchens": kitchens,
        "zones": zones,
        "categories": categories,
        "priorities": ["All Priorities", "HIGH", "MEDIUM", "LOW"],
        "statuses": ["All Statuses", "RAISED", "ASSIGNED", "IN_PROGRESS", "COMPLETED", "VERIFIED"]
    }

@app.route("/")
def home():
    """Serves the main single-page Kitchen Maintenance Dashboard."""
    return render_template("index.html")

@app.route("/api/data")
def api_data():
    """Returns live dashboard summary, charts, and tickets dataset."""
    try:
        data = prepare_dashboard_payload()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/export_csv")
def export_csv():
    """Generates and downloads a clean CSV file of tickets with optional query filters."""
    try:
        tables, _ = db_manager.fetch_live_data(tickets_only=True)
        df = tables.get("tickets", pd.DataFrame())
        
        if df.empty:
            return "No data available", 404

        # Query parameter filters
        kitchen_filter = request.args.get("kitchen")
        zone_filter = request.args.get("zone")
        area_filter = request.args.get("area")
        equipment_filter = request.args.get("equipment")
        priority_filter = request.args.get("priority")
        status_filter = request.args.get("status")
        category_filter = request.args.get("category")
        search_query = request.args.get("search", "").strip().lower()

        # Add resolved equipment column
        resolved_col = []
        for _, r in df.iterrows():
            res_eq = resolve_equipment_name(
                clean_str(r.get("equipment_name"), ""),
                clean_str(r.get("custom_equipment"), ""),
                clean_str(r.get("title"), ""),
                clean_str(r.get("area_name"), ""),
                clean_str(r.get("category"), "")
            )
            resolved_col.append(res_eq)
        df["resolved_equipment"] = resolved_col

        if kitchen_filter and kitchen_filter != "All Kitchens":
            df = df[df["kitchen_name"].astype(str).str.strip() == kitchen_filter.strip()]

        if zone_filter and zone_filter != "All Zones":
            df = df[df["zone_name"].astype(str).str.strip() == zone_filter.strip()]

        if area_filter and area_filter != "All Areas":
            df = df[df["area_name"].astype(str).str.strip() == area_filter.strip()]

        if equipment_filter and equipment_filter != "All Equipment":
            df = df[
                (df["equipment_name"].astype(str).str.strip() == equipment_filter.strip()) |
                (df["resolved_equipment"].astype(str).str.strip() == equipment_filter.strip())
            ]

        if priority_filter and priority_filter != "All Priorities":
            df = df[df["priority"].astype(str).str.upper() == priority_filter.upper()]

        if status_filter and status_filter != "All Statuses":
            if status_filter == "PENDING":
                df = df[df["status"].astype(str).str.upper().isin(["RAISED", "ASSIGNED", "IN_PROGRESS", "PENDING_SPARES"])]
            else:
                df = df[df["status"].astype(str).str.upper() == status_filter.upper()]

        if category_filter and category_filter != "All Categories":
            df = df[df["category"].astype(str).str.strip() == category_filter.strip()]

        if search_query:
            mask = (
                df["ticket_no"].astype(str).lower().str.contains(search_query) |
                df["title"].astype(str).lower().str.contains(search_query) |
                df["resolved_equipment"].astype(str).lower().str.contains(search_query) |
                df["kitchen_name"].astype(str).lower().str.contains(search_query) |
                df["zone_name"].astype(str).lower().str.contains(search_query) |
                df["area_name"].astype(str).lower().str.contains(search_query) |
                df["technician_name"].astype(str).lower().str.contains(search_query) |
                df["raised_by_name"].astype(str).lower().str.contains(search_query)
            )
            df = df[mask]
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        headers = [
            "Ticket #", "Kitchen", "Zone", "Area / Section", "Machine / Asset", "Issue Description", 
            "Status", "Priority", "Complaint Raised Time", "Assign Time", "Start Delay", 
            "Start Time", "Time to Fix (MTTR)", "Completion Time", "Action Taken by Tech", 
            "Assigned Technician", "Raised By", "Dual Verified Status", "Root Cause of Issue"
        ]
        writer.writerow(headers)

        for _, r in df.iterrows():
            m_mins = r.get("mttr_mins")
            m_hours = r.get("mttr_hours")
            mttr_dhm = format_minutes_to_dhm(m_mins) if pd.notna(m_mins) else format_hours_to_dhm(m_hours)
            resp_dhm = format_minutes_to_dhm(r.get("response_delay_mins"))

            is_raiser = bool(r.get("is_raiser_verified", False) or r.get("raiser_verified", False))
            is_admin = bool(r.get("is_admin_verified", False) or r.get("admin_verified", False))
            dual_status = "Dual Verified" if (is_raiser and is_admin) else ("Partial Sign-off" if (is_raiser or is_admin) else "Pending")

            tech_name = str(r.get("technician_name") or "Unassigned")
            if tech_name == "⏳ Unassigned":
                tech_name = "Unassigned"

            history_data = safe_json_load(r.get("status_history_json"))
            assign_time_val = extract_assigned_time(r, history_data)

            writer.writerow([
                clean_str(r.get("ticket_no"), ""),
                clean_str(r.get("kitchen_name"), ""),
                clean_str(r.get("zone_name"), "—"),
                clean_str(r.get("area_name"), "—"),
                clean_str(r.get("resolved_equipment") or r.get("equipment_name"), ""),
                clean_str(r.get("title"), ""),
                clean_str(r.get("status"), ""),
                clean_str(r.get("priority"), ""),
                clean_str(r.get("ticket_raised_time"), "—"),
                clean_str(r.get("assigned_to_time"), assign_time_val),
                clean_str(resp_dhm, "—"),
                clean_str(r.get("repair_start_time"), "—"),
                clean_str(mttr_dhm, "—"),
                clean_str(r.get("ticket_completion_time"), "—"),
                clean_str(r.get("action_taken"), "Under diagnostics"),
                tech_name,
                clean_str(r.get("raised_by_name"), "Staff"),
                dual_status,
                clean_str(r.get("cause_of_issue"), "Under diagnostics")
            ])

        output.seek(0)
        filename = "pmt_filtered_report.csv" if (kitchen_filter or zone_filter or area_filter or equipment_filter or status_filter) else "pmt_all_tickets.csv"
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename={filename}"}
        )
    except Exception as e:
        return f"Error exporting CSV: {e}", 500

if __name__ == "__main__":
    print("\n" + "="*60)
    print("[*] PMT Analysis — Plant Maintenance & Equipment Analytics")
    print("[*] Running live on: http://127.0.0.1:5000")
    print("="*60 + "\n")
    app.run(host="127.0.0.1", port=5000, debug=False)
