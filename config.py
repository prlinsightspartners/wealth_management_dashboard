# -*- coding: utf-8 -*-
"""
Global configuration for the Wealth & Asset Management Executive Dashboard.
Centralizes table names, color palette, and shared page settings so every
page renders consistently.
"""

# ---------------------------------------------------------------------------
# Supabase table names (must match the tables created via sql/schema.sql)
# ---------------------------------------------------------------------------
TBL_ADVISORS = "Investmentadvisors"
TBL_CLIENTS = "Clients"
TBL_ACCOUNTS = "Accounts"
TBL_PORTFOLIOS = "Portfolios"
TBL_ASSETS = "Assets"
TBL_HOLDINGS = "Portfolioholdings"
TBL_TRANSACTIONS = "Transactions"
TBL_INTERACTIONS = "Clientinteractions"
TBL_PORTFOLIO_METRICS = "Portfolioperformancemetrics"
TBL_ADVISOR_METRICS = "Advisorperformancemetrics"
SUPABASE_SCHEMA = "asset_management"

# Columns required by the dashboard loaders and calculations.
REQUIRED_COLUMNS = {
    TBL_ADVISORS: ["AdvisorID", "FirstName", "LastName", "Status", "HireDate"],
    TBL_CLIENTS: ["ClientID", "AdvisorID", "FirstName", "LastName", "DateOfBirth", "RegistrationDate", "City", "State", "RiskTolerance"],
    TBL_ACCOUNTS: ["AccountID", "ClientID", "AccountType", "Balance"],
    TBL_PORTFOLIOS: ["PortfolioID", "AccountID", "PortfolioName", "InvestmentStrategy", "LastRebalanceDate"],
    TBL_ASSETS: ["AssetID", "AssetName", "AssetType", "TickerSymbol"],
    TBL_HOLDINGS: ["HoldingID", "PortfolioID", "AssetID", "Quantity", "PurchasePrice", "CurrentPrice"],
    TBL_TRANSACTIONS: ["TransactionID", "AccountID", "AssetID", "TransactionType", "TransactionDate", "Quantity", "PricePerUnit", "Amount", "Commission"],
    TBL_INTERACTIONS: ["InteractionID", "ClientID", "AdvisorID", "InteractionDate", "InteractionType", "FollowUpDate"],
    TBL_PORTFOLIO_METRICS: ["MetricID", "PortfolioID", "AUM", "ReturnAbsolute", "SharpeRatio", "Beta", "CalculationDate"],
    TBL_ADVISOR_METRICS: ["MetricID", "AdvisorID", "TotalAUM", "AverageClientReturn", "NumberOfClients", "CalculationDate"],
}

REQUIRED_NONEMPTY_TABLES = [TBL_ADVISORS, TBL_CLIENTS, TBL_ACCOUNTS, TBL_PORTFOLIOS, TBL_ASSETS, TBL_HOLDINGS]

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
