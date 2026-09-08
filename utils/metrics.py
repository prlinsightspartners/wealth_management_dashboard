# -*- coding: utf-8 -*-
"""
Pure computation functions that turn raw table DataFrames into the metrics
shown on the dashboard. Kept separate from data_loader (I/O) and app pages
(presentation) so the logic is easy to test and reuse across pages.
"""
from typing import Optional

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------
def latest_snapshot(df: pd.DataFrame, group_col: str, date_col: str) -> pd.DataFrame:
    """Return only the most-recent row per group_col, based on date_col."""
    if df.empty:
        return df
    return (
        df.sort_values(date_col)
        .groupby(group_col, as_index=False)
        .tail(1)
        .reset_index(drop=True)
    )


def pct_change_over_window(df: pd.DataFrame, group_col: str, value_col: str, date_col: str) -> pd.DataFrame:
    """First vs. last value per group over the loaded window -> % change."""
    if df.empty:
        return pd.DataFrame(columns=[group_col, "PctChange"])
    df_sorted = df.sort_values(date_col)
    first = df_sorted.groupby(group_col)[value_col].first()
    last = df_sorted.groupby(group_col)[value_col].last()
    pct = ((last - first) / first.replace(0, np.nan)) * 100
    return pct.reset_index(name="PctChange")


# ---------------------------------------------------------------------------
# Firm-wide KPIs (Executive Summary)
# ---------------------------------------------------------------------------
def firm_kpis(clients_df, advisors_df, accounts_df, portfolios_df, pf_metrics_df, adv_metrics_df) -> dict:
    total_aum = accounts_df["Balance"].sum() if not accounts_df.empty else 0.0

    active_clients = int((clients_df.get("ClientID", pd.Series(dtype=int))).nunique()) if not clients_df.empty else 0
    active_advisors = int(advisors_df.loc[advisors_df.get("Status", "") == "Active", "AdvisorID"].nunique()) if not advisors_df.empty else 0
    total_accounts = int(accounts_df["AccountID"].nunique()) if not accounts_df.empty else 0
    total_portfolios = int(portfolios_df["PortfolioID"].nunique()) if not portfolios_df.empty else 0

    avg_client_return = np.nan
    if not adv_metrics_df.empty:
        latest_month = adv_metrics_df["CalculationDate"].max()
        avg_client_return = adv_metrics_df.loc[
            adv_metrics_df["CalculationDate"] == latest_month, "AverageClientReturn"
        ].mean()

    avg_sharpe = np.nan
    if not pf_metrics_df.empty:
        latest_pf_month = pf_metrics_df["CalculationDate"].max()
        avg_sharpe = pf_metrics_df.loc[
            pf_metrics_df["CalculationDate"] == latest_pf_month, "SharpeRatio"
        ].mean()

    avg_accounts_per_client = (total_accounts / active_clients) if active_clients else 0.0
    avg_aum_per_advisor = (total_aum / active_advisors) if active_advisors else 0.0

    return {
        "total_aum": total_aum,
        "active_clients": active_clients,
        "active_advisors": active_advisors,
        "total_accounts": total_accounts,
        "total_portfolios": total_portfolios,
        "avg_client_return": avg_client_return,
        "avg_sharpe": avg_sharpe,
        "avg_accounts_per_client": avg_accounts_per_client,
        "avg_aum_per_advisor": avg_aum_per_advisor,
    }


def aum_trend(pf_metrics_df: pd.DataFrame) -> pd.DataFrame:
    """Firm-wide AUM by calendar month, summed across all portfolios."""
    if pf_metrics_df.empty:
        return pd.DataFrame(columns=["CalculationDate", "AUM"])
    return (
        pf_metrics_df.groupby("CalculationDate", as_index=False)["AUM"]
        .sum()
        .sort_values("CalculationDate")
    )


def advisor_leaderboard(adv_metrics_df: pd.DataFrame, advisors_df: pd.DataFrame) -> pd.DataFrame:
    """Latest month per advisor, joined with advisor bio info."""
    if adv_metrics_df.empty or advisors_df.empty:
        return pd.DataFrame()
    latest = latest_snapshot(adv_metrics_df, "AdvisorID", "CalculationDate")
    merged = latest.merge(advisors_df, on="AdvisorID", how="left")
    merged["AdvisorName"] = merged["FirstName"] + " " + merged["LastName"]
    return merged.sort_values("TotalAUM", ascending=False)


def portfolio_leaderboard(pf_metrics_df: pd.DataFrame, portfolios_df: pd.DataFrame) -> pd.DataFrame:
    """Latest month per portfolio, joined with portfolio info."""
    if pf_metrics_df.empty or portfolios_df.empty:
        return pd.DataFrame()
    latest = latest_snapshot(pf_metrics_df, "PortfolioID", "CalculationDate")
    merged = latest.merge(portfolios_df, on="PortfolioID", how="left")
    return merged.sort_values("ReturnAbsolute", ascending=False)


def asset_allocation(holdings_df: pd.DataFrame, assets_df: pd.DataFrame) -> pd.DataFrame:
    """Current market value of every holding, grouped by asset type."""
    if holdings_df.empty or assets_df.empty:
        return pd.DataFrame(columns=["AssetType", "MarketValue", "Weight"])
    merged = holdings_df.merge(assets_df, on="AssetID", how="left")
    merged["MarketValue"] = merged["Quantity"] * merged["CurrentPrice"]
    grouped = merged.groupby("AssetType", as_index=False)["MarketValue"].sum()
    total = grouped["MarketValue"].sum()
    grouped["Weight"] = grouped["MarketValue"] / total if total else 0
    return grouped.sort_values("MarketValue", ascending=False)


def top_holdings(holdings_df: pd.DataFrame, assets_df: pd.DataFrame, n: int = 15) -> pd.DataFrame:
    if holdings_df.empty or assets_df.empty:
        return pd.DataFrame()
    merged = holdings_df.merge(assets_df, on="AssetID", how="left")
    merged["MarketValue"] = merged["Quantity"] * merged["CurrentPrice"]
    grouped = (
        merged.groupby(["AssetID", "AssetName", "TickerSymbol", "AssetType"], as_index=False)
        .agg(TotalMarketValue=("MarketValue", "sum"), PositionsHeld=("HoldingID", "count"))
        .sort_values("TotalMarketValue", ascending=False)
        .head(n)
    )
    return grouped


def concentration_risk(holdings_df: pd.DataFrame, assets_df: pd.DataFrame, top_n: int = 10) -> float:
    """Share of total firm AUM held in the top N positions — a concentration risk gauge."""
    top_df = top_holdings(holdings_df, assets_df, n=top_n)
    if top_df.empty:
        return 0.0
    all_merged = holdings_df.merge(assets_df, on="AssetID", how="left")
    all_merged["MarketValue"] = all_merged["Quantity"] * all_merged["CurrentPrice"]
    total = all_merged["MarketValue"].sum()
    return (top_df["TotalMarketValue"].sum() / total * 100) if total else 0.0


def client_growth(clients_df: pd.DataFrame) -> pd.DataFrame:
    """Cumulative client count over time, by registration month."""
    if clients_df.empty:
        return pd.DataFrame(columns=["Month", "NewClients", "CumulativeClients"])
    df = clients_df.copy()
    df["Month"] = pd.to_datetime(df["RegistrationDate"]).dt.to_period("M").dt.to_timestamp()
    monthly = df.groupby("Month", as_index=False).size().rename(columns={"size": "NewClients"})
    monthly = monthly.sort_values("Month")
    monthly["CumulativeClients"] = monthly["NewClients"].cumsum()
    return monthly


def risk_tolerance_distribution(clients_df: pd.DataFrame) -> pd.DataFrame:
    if clients_df.empty:
        return pd.DataFrame(columns=["RiskTolerance", "Count"])
    return clients_df["RiskTolerance"].value_counts().rename_axis("RiskTolerance").reset_index(name="Count")


def province_distribution(clients_df: pd.DataFrame, accounts_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    if clients_df.empty:
        return pd.DataFrame(columns=["State", "Clients"])
    out = clients_df["State"].value_counts().rename_axis("State").reset_index(name="Clients")
    if accounts_df is not None and not accounts_df.empty:
        acc_by_client = accounts_df.groupby("ClientID")["Balance"].sum().reset_index()
        joined = clients_df[["ClientID", "State"]].merge(acc_by_client, on="ClientID", how="left")
        aum_by_prov = joined.groupby("State", as_index=False)["Balance"].sum().rename(columns={"Balance": "AUM"})
        out = out.merge(aum_by_prov, on="State", how="left")
    return out.sort_values("Clients", ascending=False)


def interaction_summary(interactions_df: pd.DataFrame) -> dict:
    if interactions_df.empty:
        return {"total": 0, "by_type": pd.DataFrame(), "pending_followups": 0, "monthly": pd.DataFrame()}
    total = len(interactions_df)
    by_type = interactions_df["InteractionType"].value_counts().rename_axis("InteractionType").reset_index(name="Count")
    pending = interactions_df["FollowUpDate"].notna().sum() if "FollowUpDate" in interactions_df.columns else 0
    df = interactions_df.copy()
    df["Month"] = pd.to_datetime(df["InteractionDate"]).dt.to_period("M").dt.to_timestamp()
    monthly = df.groupby("Month", as_index=False).size().rename(columns={"size": "Interactions"})
    return {"total": total, "by_type": by_type, "pending_followups": int(pending), "monthly": monthly}


def transaction_summary(transactions_df: pd.DataFrame) -> dict:
    if transactions_df.empty:
        return {"total_volume": 0.0, "total_commission": 0.0, "by_type": pd.DataFrame(), "monthly": pd.DataFrame()}
    total_volume = transactions_df["Amount"].abs().sum()
    total_commission = transactions_df["Commission"].sum()
    by_type = (
        transactions_df.groupby("TransactionType")["Amount"]
        .agg(["count", "sum"])
        .reset_index()
        .rename(columns={"count": "Count", "sum": "TotalAmount"})
    )
    by_type["TotalAmount"] = transactions_df.groupby("TransactionType")["Amount"].apply(lambda x: x.abs().sum()).values
    df = transactions_df.copy()
    df["Month"] = pd.to_datetime(df["TransactionDate"]).dt.to_period("M").dt.to_timestamp()
    monthly = df.groupby("Month", as_index=False)["Amount"].apply(lambda x: x.abs().sum()).rename(columns={"Amount": "Volume"})
    return {
        "total_volume": total_volume,
        "total_commission": total_commission,
        "by_type": by_type,
        "monthly": monthly,
    }


def strategy_breakdown(portfolios_df: pd.DataFrame, pf_metrics_df: pd.DataFrame) -> pd.DataFrame:
    """Latest AUM and average return per investment strategy."""
    if portfolios_df.empty or pf_metrics_df.empty:
        return pd.DataFrame()
    latest = latest_snapshot(pf_metrics_df, "PortfolioID", "CalculationDate")
    merged = latest.merge(portfolios_df[["PortfolioID", "InvestmentStrategy"]], on="PortfolioID", how="left")
    grouped = merged.groupby("InvestmentStrategy", as_index=False).agg(
        AUM=("AUM", "sum"),
        AvgReturn=("ReturnAbsolute", "mean"),
        AvgSharpe=("SharpeRatio", "mean"),
        PortfolioCount=("PortfolioID", "nunique"),
    )
    return grouped.sort_values("AUM", ascending=False)
