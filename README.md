# ⚙️ Enterprise Kitchen & Plant Maintenance (PMT) Analytics Dashboard

A production-grade Python CMMS (Computerized Maintenance Management System) analytics dashboard built with **Streamlit**, **Plotly**, and **Pandas**, tailored to your PostgreSQL/Supabase database schema.

---

## 📁 Aligned Project Folder Structure

```
PMT Analysis/
├── .env                  # Live environment variables & database configuration
├── .env.example          # Template configuration
├── requirements.txt      # Python dependencies
├── run.bat               # Windows one-click launcher
├── app.py                # Main Streamlit Application entry point
├── config/
│   ├── __init__.py
│   └── settings.py       # Centralized settings & environment loader
├── src/
│   ├── __init__.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py # Supabase/Postgres connection with fallback handler
│   │   └── mock_data.py  # Realistic 20+ table schema-synchronized dataset
│   ├── analytics/
│   │   ├── __init__.py
│   │   ├── kpis.py       # MTTR, Downtime, PM Ratio, Dual Verification
│   │   ├── pareto.py     # Pareto 80/20 bad actor calculations & categories
│   │   ├── spares.py     # Spare burn rate, stockouts, critical risk alerts
│   │   ├── technicians.py# SLA compliance, resolution velocity, tool checkouts
│   │   └── utilities.py  # Boiler & electrical log correlations
│   └── ui/
│       ├── __init__.py
│       ├── theme.py      # Custom dark/light styling, cards, status badges
│       └── components/
│           ├── __init__.py
│           ├── filters.py        # Multi-facet cascading sidebar filters
│           ├── kpi_cards.py      # 6 executive KPI summary cards
│           ├── ticket_explorer.py# Searchable table, timeline, photo proofs
│           ├── pareto_view.py    # Plotly Pareto 80/20 & Asset health matrix
│           ├── spares_view.py    # Spares inventory & depletion alerts
│           ├── technician_view.py# Technician SLA & tool custody tracker
│           └── utility_view.py   # Utility logbook breakdown correlations
└── README.md
```

---

## 🚀 Quick Start Guide

You have two dashboard interfaces available:

### 1. Executive Kitchen Maintenance Hub (Flask Web App)
A fast, responsive single-page application with modern cards, status pipelines, search, and CSV export.
* **One-Click**: Double-click `run_flask.bat`
* **Command Line**:
  ```powershell
  python flask_app.py
  ```
* **URL**: [http://127.0.0.1:5000](http://127.0.0.1:5000)

### 2. Comprehensive Analytics Dashboard (Streamlit)
A multi-tab deep-dive analytics dashboard with interactive Plotly charts, Pareto 80/20 analysis, and SLA breakdowns.
* **One-Click**: Double-click `run.bat`
* **Command Line**:
  ```powershell
  python -m streamlit run app.py
  ```
* **URL**: [http://localhost:8501](http://localhost:8501)

---

## 🔌 Connecting to your Live Supabase / PostgreSQL Database

1. Open `.env` in this directory:
   ```env
   USE_MOCK_DATA=false
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-supabase-service-or-anon-key
   ```
2. Restart the app (`python -m streamlit run app.py`). The dashboard will seamlessly pull live tables from your Supabase instance.

---

## 📊 Standard Operational Calculations Implemented

| Metric | Business Definition | Schema Mapping |
| :--- | :--- | :--- |
| **MTTR** | Mean Time To Repair | `AVG(ticket_completion_time - repair_start_time)` |
| **Total Downtime** | Total production outage | `SUM(ticket_completion_time - breakdown_time)` |
| **Response Time** | Time to dispatch technician | `AVG(repair_start_time - ticket_raised_time)` |
| **PM vs CM Ratio** | Preventive vs Breakdown ratio | `Planned PM Tasks / (Planned PM + Breakdown Tickets)` |
| **Dual Verification %**| Governance audit compliance | `tickets WHERE admin_verified = true AND raiser_verified = true` |
| **Pareto 80/20** | Top 20% assets causing 80% loss | Cumulative downtime sum over `m_equipment` |
| **Stock Alert** | Low inventory warning | `spare_tracker WHERE current_qty <= min_qty_alert` |
| **Tool Custody** | Unreturned tool holding | `ticket_tools WHERE return_time IS NULL AND is_vacant = false` |
