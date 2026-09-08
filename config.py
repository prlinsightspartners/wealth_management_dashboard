# -*- coding: utf-8 -*-
"""
Global configuration for the Wealth & Asset Management Executive Dashboard.
Centralizes table names, color palette, and shared page settings so every
page renders consistently.
"""

# ---------------------------------------------------------------------------
# Supabase table names (must match the tables created via sql/schema.sql)
# ---------------------------------------------------------------------------
TBL_ADVISORS = "InvestmentAdvisors"
TBL_CLIENTS = "Clients"
TBL_ACCOUNTS = "Accounts"
TBL_PORTFOLIOS = "Portfolios"
TBL_ASSETS = "Assets"
TBL_HOLDINGS = "PortfolioHoldings"
TBL_TRANSACTIONS = "Transactions"
TBL_INTERACTIONS = "ClientInteractions"
TBL_PORTFOLIO_METRICS = "PortfolioPerformanceMetrics"
TBL_ADVISOR_METRICS = "AdvisorPerformanceMetrics"

# ---------------------------------------------------------------------------
# App-wide settings
# ---------------------------------------------------------------------------
APP_TITLE = "Wealth & Asset Management — Executive Dashboard"
APP_ICON = "📊"
FIRM_NAME = "Northbridge Wealth Partners"
CACHE_TTL_SECONDS = 600  # 10 minutes; data refresh cadence for cached Supabase pulls

# How much transaction / holdings history to pull by default (keeps the app snappy
# on large tables). Users can widen this from the sidebar on the relevant pages.
DEFAULT_LOOKBACK_MONTHS = 24

# ---------------------------------------------------------------------------
# Color palette — professional navy / gold institutional finance theme
# ---------------------------------------------------------------------------
COLOR_PRIMARY = "#0B2545"      # deep navy
COLOR_SECONDARY = "#13315C"    # navy accent
COLOR_ACCENT = "#C9A227"       # gold
COLOR_POSITIVE = "#1E8A5F"     # green (gains)
COLOR_NEGATIVE = "#B23A48"     # muted red (losses)
COLOR_NEUTRAL = "#8D99AE"      # slate gray
COLOR_BACKGROUND = "#F5F7FA"
COLOR_CARD_BG = "#FFFFFF"

CATEGORICAL_PALETTE = [
    "#0B2545", "#C9A227", "#13315C", "#1E8A5F", "#8D99AE",
    "#B23A48", "#3E6990", "#E1B12C", "#5C7285", "#7A9E9F",
]

PLOTLY_TEMPLATE = "plotly_white"

# Canonical ordering for risk tolerance / display consistency
RISK_ORDER = ["Conservative", "Moderately Conservative", "Moderate",
              "Moderately Aggressive", "Aggressive"]

PROVINCE_ORDER = ["ON", "QC", "BC", "AB", "MB", "SK", "NS", "NB", "NL", "PE", "YT", "NT", "NU"]
