import os
import pandas as pd
from typing import Dict, Optional, Tuple
from config.settings import settings

class DatabaseManager:
    """
    Live Supabase Database Connection Layer:
    - Queries the centralized PostgreSQL view `v_pmt_dashboard_tickets`.
    - Fetches live auxiliary tables for inventory, schedules, and utility logbooks.
    """
    def __init__(self):
        self._supabase_client = None
        self._initialize_client()

    def _initialize_client(self):
        if settings.SUPABASE_URL and settings.SUPABASE_KEY:
            try:
                from supabase import create_client
                self._supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            except Exception as e:
                print(f"[DB] Error initializing Supabase client: {e}")
                self._supabase_client = None

    def fetch_live_data(self, tickets_only: bool = False) -> Tuple[Dict[str, pd.DataFrame], str]:
        """
        Fetches live tables and views directly from Supabase.
        Returns: (tables_dict, status_description)
        """
        if self._supabase_client is None:
            self._initialize_client()
            if self._supabase_client is None:
                return {}, "❌ Supabase Credentials Missing or Invalid"

        try:
            live_data = {}
            
            # 1. Fetch from Central Unified View: v_pmt_dashboard_tickets
            try:
                res_view = self._supabase_client.table("v_pmt_dashboard_tickets").select("*").execute()
                df_tickets = pd.DataFrame(res_view.data) if res_view.data else pd.DataFrame()
                live_data["tickets"] = df_tickets
                live_data["v_pmt_dashboard_tickets"] = df_tickets
            except Exception as e_view:
                print(f"[DB] Error reading v_pmt_dashboard_tickets: {e_view}")
                try:
                    res_t = self._supabase_client.table("tickets").select("*").execute()
                    live_data["tickets"] = pd.DataFrame(res_t.data) if res_t.data else pd.DataFrame()
                except Exception:
                    live_data["tickets"] = pd.DataFrame()

            # 2. Fetch Auxiliary Master & Transaction Tables (if requested)
            if not tickets_only:
                tables_to_query = [
                    "m_cluster", "m_kitchen", "m_zone", "m_area", "m_user",
                    "m_equipment", "m_spares", "spare_tracker", "m_tools",
                    "ticket_status_history", "spare_ticket", "ticket_tools",
                    "ticket_media", "rep_preventive_machine_schedule",
                    "daily_boiler_log", "daily_electrical_log"
                ]
                for tbl in tables_to_query:
                    try:
                        res = self._supabase_client.table(tbl).select("*").execute()
                        live_data[tbl] = pd.DataFrame(res.data) if res.data else pd.DataFrame()
                    except Exception:
                        live_data[tbl] = pd.DataFrame()
            else:
                # Provide empty DataFrames for expected keys
                for tbl in ["m_cluster", "m_kitchen", "m_zone", "m_area", "m_user",
                            "m_equipment", "m_spares", "spare_tracker", "m_tools",
                            "ticket_status_history", "spare_ticket", "ticket_tools",
                            "ticket_media", "rep_preventive_machine_schedule",
                            "daily_boiler_log", "daily_electrical_log"]:
                    live_data[tbl] = pd.DataFrame()

            ticket_count = len(live_data.get("tickets", []))
            status_desc = f"🟢 Connected to Live Supabase ({ticket_count} tickets)"
            return live_data, status_desc

        except Exception as e:
            print(f"[DB] Error querying Supabase: {e}")
            return {}, f"❌ Connection Error: {str(e)}"

    def fetch_data(self, use_mock: bool = False) -> Tuple[Dict[str, pd.DataFrame], str]:
        """Backward compatibility alias."""
        return self.fetch_live_data()

    def get_all_tables(self) -> Dict[str, pd.DataFrame]:
        """Backward compatibility alias."""
        tables, _ = self.fetch_live_data()
        return tables

    def get_table(self, table_name: str) -> pd.DataFrame:
        """Fetch single table."""
        tables, _ = self.fetch_live_data()
        return tables.get(table_name, pd.DataFrame())

db_manager = DatabaseManager()
