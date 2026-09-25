import streamlit as st

def apply_custom_theme():
    """
    Applies clean, modern, executive-friendly CSS for Rasoi Ops Kitchen CMMS.
    Designed for maximum clarity, low cognitive load, and great contrast in Light/Dark modes.
    """
    st.markdown("""
        <style>
        /* Base page container */
        .block-container {
            padding-top: 1.2rem !important;
            padding-bottom: 2.5rem !important;
            max-width: 95% !important;
        }

        /* Top Brand Header Banner */
        .rasoi-header-banner {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: linear-gradient(135deg, rgba(249, 115, 22, 0.08) 0%, rgba(59, 130, 246, 0.06) 100%);
            border: 1px solid rgba(249, 115, 22, 0.2);
            border-radius: 14px;
            padding: 16px 24px;
            margin-bottom: 20px;
        }
        .rasoi-brand-title {
            font-size: 1.9rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            margin: 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .rasoi-brand-sub {
            font-size: 0.9rem;
            opacity: 0.75;
            margin-top: 4px;
            margin-bottom: 0;
        }

        /* Modern Executive KPI Metric Cards */
        div[data-testid="stMetric"] {
            border: 1px solid rgba(128, 128, 128, 0.18) !important;
            border-radius: 12px !important;
            padding: 16px 20px !important;
            background: rgba(128, 128, 128, 0.04) !important;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.03) !important;
            transition: all 0.2s ease-in-out !important;
        }
        div[data-testid="stMetric"]:hover {
            border-color: #f97316 !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 18px rgba(249, 115, 22, 0.1) !important;
        }

        div[data-testid="stMetricValue"] > div {
            font-size: 1.7rem !important;
            font-weight: 800 !important;
            white-space: normal !important;
            line-height: 1.2 !important;
            color: inherit !important;
        }
        div[data-testid="stMetricLabel"] > div > p {
            font-size: 0.82rem !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
            opacity: 0.8 !important;
            margin-bottom: 4px !important;
        }
        div[data-testid="stMetricDelta"] > div {
            font-size: 0.8rem !important;
            font-weight: 600 !important;
        }

        /* Clean Tab styling */
        button[data-baseweb="tab"] {
            font-size: 0.98rem !important;
            font-weight: 600 !important;
            padding: 10px 20px !important;
            border-radius: 8px 8px 0 0 !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            border-bottom: 3px solid #f97316 !important;
            color: #f97316 !important;
        }

        /* Simplified Status Pills */
        .pill {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 0.76rem;
            font-weight: 700;
            text-align: center;
        }
        .pill-active { background: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.3); }
        .pill-resolved { background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); }
        .pill-progress { background: rgba(245, 158, 11, 0.15); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.3); }
        .pill-info { background: rgba(59, 130, 246, 0.15); color: #3b82f6; border: 1px solid rgba(59, 130, 246, 0.3); }

        /* Inspection Card */
        .ticket-detail-box {
            border: 1px solid rgba(128, 128, 128, 0.22);
            border-radius: 12px;
            padding: 20px 24px;
            margin: 15px 0;
            background: rgba(128, 128, 128, 0.03);
        }

        /* Dataframe border polish */
        div[data-testid="stDataFrame"] {
            border-radius: 10px;
            border: 1px solid rgba(128, 128, 128, 0.15);
        }

        /* Sidebar clean styling */
        section[data-testid="stSidebar"] {
            border-right: 1px solid rgba(128, 128, 128, 0.15);
        }
        </style>
    """, unsafe_allow_html=True)
