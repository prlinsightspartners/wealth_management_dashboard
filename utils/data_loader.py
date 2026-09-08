# -*- coding: utf-8 -*-
"""
Cached loaders for each Supabase table. Every function returns a clean
pandas DataFrame with date/datetime columns parsed. Results are cached with
st.cache_data so repeated page visits within the TTL window don't re-hit
Supabase.

Heavy tables (Transactions, PortfolioHoldings, PortfolioPerformanceMetrics)
accept a `months_back` argument that pushes a date filter down to the
Supabase query itself, rather than pulling the full table and filtering
client-side.
"""
from datetime import date, timedelta
from typing import Optional

import pandas as pd
import streamlit as st

from db.supabase_client import fetch_all
import config as cfg


def _parse_dates(df: pd.DataFrame, date_cols=(), datetime_cols=()) -> pd.DataFrame:
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.date
    for col in datetime_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def _cutoff(months_back: Optional[int]) -> Optional[str]:
    if months_back is None:
        return None
    cutoff = date.today() - timedelta(days=int(months_back) * 30.44)
    return cutoff.isoformat()


# ---------------------------------------------------------------------------
# Core / low-volume tables
# ---------------------------------------------------------------------------
@st.cache_data(ttl=cfg.CACHE_TTL_SECONDS, show_spinner="Loading advisors…")
def load_advisors() -> pd.DataFrame:
    df = fetch_all(cfg.TBL_ADVISORS)
    return _parse_dates(df, date_cols=["HireDate"])


@st.cache_data(ttl=cfg.CACHE_TTL_SECONDS, show_spinner="Loading clients…")
def load_clients() -> pd.DataFrame:
    df = fetch_all(cfg.TBL_CLIENTS)
    df = _parse_dates(df, date_cols=["DateOfBirth", "RegistrationDate"])
    if "DateOfBirth" in df.columns:
        today = date.today()
        df["Age"] = df["DateOfBirth"].apply(
            lambda d: today.year - d.year - ((today.month, today.day) < (d.month, d.day))
            if pd.notnull(d) else None
        )
    return df


@st.cache_data(ttl=cfg.CACHE_TTL_SECONDS, show_spinner="Loading accounts…")
def load_accounts() -> pd.DataFrame:
    df = fetch_all(cfg.TBL_ACCOUNTS)
    return _parse_dates(df, date_cols=["OpeningDate"])


@st.cache_data(ttl=cfg.CACHE_TTL_SECONDS, show_spinner="Loading portfolios…")
def load_portfolios() -> pd.DataFrame:
    df = fetch_all(cfg.TBL_PORTFOLIOS)
    return _parse_dates(df, date_cols=["CreationDate", "LastRebalanceDate"])


@st.cache_data(ttl=cfg.CACHE_TTL_SECONDS, show_spinner="Loading asset universe…")
def load_assets() -> pd.DataFrame:
    return fetch_all(cfg.TBL_ASSETS)


@st.cache_data(ttl=cfg.CACHE_TTL_SECONDS, show_spinner="Loading client interactions…")
def load_interactions(months_back: Optional[int] = None) -> pd.DataFrame:
    filters = None
    cutoff = _cutoff(months_back)
    if cutoff:
        filters = [lambda q: q.gte("InteractionDate", cutoff)]
    df = fetch_all(cfg.TBL_INTERACTIONS, filters=filters)
    return _parse_dates(df, date_cols=["FollowUpDate"], datetime_cols=["InteractionDate"])


# ---------------------------------------------------------------------------
# Heavier tables — support a lookback window to keep payloads manageable
# ---------------------------------------------------------------------------
@st.cache_data(ttl=cfg.CACHE_TTL_SECONDS, show_spinner="Loading portfolio holdings…")
def load_holdings() -> pd.DataFrame:
    # Holdings represent current positions, not a time series — always load in full.
    df = fetch_all(cfg.TBL_HOLDINGS)
    return _parse_dates(df, date_cols=["PurchaseDate"], datetime_cols=["LastUpdated"])


@st.cache_data(ttl=cfg.CACHE_TTL_SECONDS, show_spinner="Loading transactions…")
def load_transactions(months_back: Optional[int] = cfg.DEFAULT_LOOKBACK_MONTHS) -> pd.DataFrame:
    filters = None
    cutoff = _cutoff(months_back)
    if cutoff:
        filters = [lambda q: q.gte("TransactionDate", cutoff)]
    df = fetch_all(cfg.TBL_TRANSACTIONS, filters=filters, order_by="TransactionDate", ascending=False)
    return _parse_dates(df, datetime_cols=["TransactionDate"])


@st.cache_data(ttl=cfg.CACHE_TTL_SECONDS, show_spinner="Loading portfolio performance metrics…")
def load_portfolio_metrics(months_back: Optional[int] = cfg.DEFAULT_LOOKBACK_MONTHS) -> pd.DataFrame:
    filters = None
    cutoff = _cutoff(months_back)
    if cutoff:
        filters = [lambda q: q.gte("CalculationDate", cutoff)]
    df = fetch_all(cfg.TBL_PORTFOLIO_METRICS, filters=filters, order_by="CalculationDate")
    return _parse_dates(
        df, date_cols=["CalculationDate"], datetime_cols=["CreatedAt", "UpdatedAt"]
    )


@st.cache_data(ttl=cfg.CACHE_TTL_SECONDS, show_spinner="Loading advisor performance metrics…")
def load_advisor_metrics(months_back: Optional[int] = cfg.DEFAULT_LOOKBACK_MONTHS) -> pd.DataFrame:
    filters = None
    cutoff = _cutoff(months_back)
    if cutoff:
        filters = [lambda q: q.gte("CalculationDate", cutoff)]
    df = fetch_all(cfg.TBL_ADVISOR_METRICS, filters=filters, order_by="CalculationDate")
    return _parse_dates(
        df, date_cols=["CalculationDate"], datetime_cols=["CreatedAt", "UpdatedAt"]
    )


def clear_all_caches():
    """Wipe every cached loader — bound to the sidebar 'Refresh data' button."""
    st.cache_data.clear()
