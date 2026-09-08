# -*- coding: utf-8 -*-
"""Transactions & Activity — trading volume, commission revenue, and account-level activity."""
import pandas as pd
import streamlit as st

import config as cfg
from utils import data_loader as dl
from utils import metrics as mx
from utils import charts as ch
from utils.styling import inject_global_css, page_header, section_banner, kpi_card, format_currency

st.set_page_config(page_title="Transactions & Activity", page_icon="💳", layout="wide")
inject_global_css()

with st.sidebar:
    st.markdown(f"# {cfg.APP_ICON} {cfg.FIRM_NAME}")
    st.divider()
    lookback = st.select_slider("Transaction history window (months)", options=[3, 6, 12, 24], value=12)
    if st.button("🔄 Refresh data", use_container_width=True):
        dl.clear_all_caches()
        st.rerun()

transactions_df = dl.load_transactions(months_back=lookback)
assets_df = dl.load_assets()
accounts_df = dl.load_accounts()
clients_df = dl.load_clients()

page_header("Transactions & Activity", f"Trading activity over the trailing {lookback} months.")

if transactions_df.empty:
    st.info("No transactions found in the selected window.")
    st.stop()

# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------
txn_types = sorted(transactions_df["TransactionType"].dropna().unique())
f1 = st.multiselect("Transaction type", options=txn_types, default=txn_types)
filtered_txn = transactions_df[transactions_df["TransactionType"].isin(f1)] if f1 else transactions_df

# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------
summary = mx.transaction_summary(filtered_txn)
k1, k2, k3, k4 = st.columns(4)
with k1:
    kpi_card("Total Transactions", f"{len(filtered_txn):,}")
with k2:
    kpi_card("Total Trading Volume", format_currency(summary["total_volume"]))
with k3:
    kpi_card("Total Commission Revenue", format_currency(summary["total_commission"]))
with k4:
    kpi_card("Avg. Transaction Size", format_currency(filtered_txn["Amount"].abs().mean()))

st.write("")

# ---------------------------------------------------------------------------
# Volume trend + type breakdown
# ---------------------------------------------------------------------------
section_banner("Trading Volume Over Time")
v1, v2 = st.columns([2, 1])
with v1:
    if not summary["monthly"].empty:
        st.plotly_chart(ch.area_trend(summary["monthly"], "Month", "Volume", title="Monthly Trading Volume", height=400),
                         use_container_width=True)
    else:
        st.info("No monthly volume data available.")
with v2:
    if not summary["by_type"].empty:
        st.plotly_chart(ch.donut_chart(summary["by_type"], "TransactionType", "Count", title="Transactions by Type", height=400),
                         use_container_width=True)
    else:
        st.info("No transaction type data available.")

# ---------------------------------------------------------------------------
# Commission trend & asset-type activity
# ---------------------------------------------------------------------------
section_banner("Commission Revenue & Activity by Asset Type")
c1, c2 = st.columns(2)
with c1:
    comm_df = filtered_txn.copy()
    comm_df["Month"] = pd.to_datetime(comm_df["TransactionDate"]).dt.to_period("M").dt.to_timestamp()
    comm_monthly = comm_df.groupby("Month", as_index=False)["Commission"].sum()
    st.plotly_chart(ch.line_trend(comm_monthly, "Month", "Commission", title="Monthly Commission Revenue", height=380),
                     use_container_width=True)
with c2:
    txn_assets = filtered_txn.merge(assets_df, on="AssetID", how="left")
    by_asset_type = txn_assets.groupby("AssetType", as_index=False)["Amount"].apply(lambda x: x.abs().sum())
    st.plotly_chart(ch.bar_chart(by_asset_type, "AssetType", "Amount", title="Trading Volume by Asset Type", height=380),
                     use_container_width=True)

# ---------------------------------------------------------------------------
# Most active accounts / assets
# ---------------------------------------------------------------------------
section_banner("Most Active Accounts & Assets")
m1, m2 = st.columns(2)
with m1:
    st.markdown("**Top 10 Most Active Accounts (by transaction count)**")
    active_accounts = (
        filtered_txn.groupby("AccountID", as_index=False)
        .agg(TransactionCount=("TransactionID", "count"), TotalVolume=("Amount", lambda x: x.abs().sum()))
        .sort_values("TransactionCount", ascending=False)
        .head(10)
    )
    if not accounts_df.empty:
        active_accounts = active_accounts.merge(
            accounts_df[["AccountID", "AccountType", "ClientID"]], on="AccountID", how="left"
        )
    disp = active_accounts.copy()
    if "TotalVolume" in disp.columns:
        disp["TotalVolume"] = disp["TotalVolume"].apply(format_currency)
    st.dataframe(disp, hide_index=True, use_container_width=True)
with m2:
    st.markdown("**Top 10 Most Traded Assets**")
    active_assets = (
        filtered_txn.groupby("AssetID", as_index=False)
        .agg(TransactionCount=("TransactionID", "count"), TotalVolume=("Amount", lambda x: x.abs().sum()))
        .sort_values("TransactionCount", ascending=False)
        .head(10)
        .merge(assets_df, on="AssetID", how="left")
    )
    disp = active_assets[["TickerSymbol", "AssetName", "TransactionCount", "TotalVolume"]].copy()
    disp["TotalVolume"] = disp["TotalVolume"].apply(format_currency)
    disp.columns = ["Ticker", "Asset Name", "# Transactions", "Volume"]
    st.dataframe(disp, hide_index=True, use_container_width=True)

# ---------------------------------------------------------------------------
# Transaction log explorer
# ---------------------------------------------------------------------------
section_banner("Transaction Log")
search_account = st.number_input("Filter by Account ID (0 = show all)", min_value=0, value=0, step=1)
log = filtered_txn.copy()
if search_account:
    log = log[log["AccountID"] == search_account]

log = log.merge(assets_df[["AssetID", "TickerSymbol", "AssetName"]], on="AssetID", how="left")
disp_cols = ["TransactionID", "AccountID", "TickerSymbol", "AssetName", "TransactionType",
             "TransactionDate", "Quantity", "PricePerUnit", "Amount", "Commission"]
disp = log[disp_cols].sort_values("TransactionDate", ascending=False).head(500).copy()
disp["Amount"] = disp["Amount"].apply(format_currency)
disp["PricePerUnit"] = disp["PricePerUnit"].apply(lambda v: format_currency(v, compact=False))
disp["Commission"] = disp["Commission"].apply(lambda v: format_currency(v, compact=False))
disp.columns = ["Txn ID", "Account ID", "Ticker", "Asset", "Type", "Date", "Qty", "Price/Unit", "Amount", "Commission"]
st.dataframe(disp, hide_index=True, use_container_width=True, height=420)
st.caption("Showing up to 500 most recent matching transactions.")
