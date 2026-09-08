# -*- coding: utf-8 -*-
"""Asset Allocation — firm-wide positioning, concentration risk, and exchange exposure."""
import pandas as pd
import streamlit as st

import config as cfg
from utils import data_loader as dl
from utils import metrics as mx
from utils import charts as ch
from utils.styling import inject_global_css, page_header, section_banner, kpi_card, format_currency, format_pct

st.set_page_config(page_title="Asset Allocation", page_icon="💰", layout="wide")
inject_global_css()

with st.sidebar:
    st.markdown(f"# {cfg.APP_ICON} {cfg.FIRM_NAME}")
    st.divider()
    if st.button("🔄 Refresh data", use_container_width=True):
        dl.clear_all_caches()
        st.rerun()

holdings_df = dl.load_holdings()
assets_df = dl.load_assets()
portfolios_df = dl.load_portfolios()

page_header("Asset Allocation", "Current positioning across asset classes, exchanges, and individual holdings.")

if holdings_df.empty or assets_df.empty:
    st.info("No holdings data available.")
    st.stop()

merged = holdings_df.merge(assets_df, on="AssetID", how="left")
merged["MarketValue"] = merged["Quantity"] * merged["CurrentPrice"]
merged["UnrealizedGain"] = (merged["CurrentPrice"] - merged["PurchasePrice"]) * merged["Quantity"]
merged["UnrealizedGainPct"] = (merged["CurrentPrice"] - merged["PurchasePrice"]) / merged["PurchasePrice"]

# Infer exchange from ticker suffix — a lightweight heuristic (".TO" = TSX, else NASDAQ/NYSE/other)
def infer_exchange(row):
    ticker = str(row.get("TickerSymbol", ""))
    if ticker.endswith(".TO"):
        return "TSX (Canada)"
    if row.get("AssetType") == "Currency":
        return "FX Market"
    if row.get("AssetType") == "Commodity":
        return "Commodities Market"
    if row.get("AssetType") == "Fixed Income":
        return "Bond Market"
    return "US Exchanges (NYSE/NASDAQ)"

merged["Exchange"] = merged.apply(infer_exchange, axis=1)

# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------
total_mv = merged["MarketValue"].sum()
total_gain = merged["UnrealizedGain"].sum()
concentration = mx.concentration_risk(holdings_df, assets_df, top_n=10)

k1, k2, k3, k4 = st.columns(4)
with k1:
    kpi_card("Total Market Value", format_currency(total_mv))
with k2:
    kpi_card("Unrealized Gain / (Loss)", format_currency(total_gain), positive=total_gain >= 0)
with k3:
    kpi_card("Top-10 Position Concentration", f"{concentration:.1f}%")
with k4:
    kpi_card("Distinct Assets Held", f"{merged['AssetID'].nunique():,}")

st.write("")

# ---------------------------------------------------------------------------
# Allocation views
# ---------------------------------------------------------------------------
section_banner("Allocation Mix")
a1, a2 = st.columns(2)
with a1:
    alloc = mx.asset_allocation(holdings_df, assets_df)
    st.plotly_chart(ch.donut_chart(alloc, "AssetType", "MarketValue", title="By Asset Type", height=400), use_container_width=True)
with a2:
    exch = merged.groupby("Exchange", as_index=False)["MarketValue"].sum()
    st.plotly_chart(ch.donut_chart(exch, "Exchange", "MarketValue", title="By Exchange / Market", height=400), use_container_width=True)

# ---------------------------------------------------------------------------
# Top holdings & concentration
# ---------------------------------------------------------------------------
section_banner("Top Holdings (Firm-Wide)")
top_n = st.slider("Show top N holdings", min_value=5, max_value=30, value=15, step=5)
top_hold = mx.top_holdings(holdings_df, assets_df, n=top_n)
if not top_hold.empty:
    t1, t2 = st.columns([2, 1])
    with t1:
        st.plotly_chart(
            ch.bar_chart(top_hold, "AssetName", "TotalMarketValue", title=f"Top {top_n} Positions by Market Value",
                         horizontal=True, height=max(400, top_n * 22)),
            use_container_width=True,
        )
    with t2:
        disp = top_hold[["TickerSymbol", "AssetType", "TotalMarketValue", "PositionsHeld"]].copy()
        disp["TotalMarketValue"] = disp["TotalMarketValue"].apply(format_currency)
        disp.columns = ["Ticker", "Type", "Market Value", "# Positions"]
        st.dataframe(disp, hide_index=True, use_container_width=True, height=max(400, top_n * 22))
else:
    st.info("No holdings data available.")

# ---------------------------------------------------------------------------
# Gain/Loss by asset type
# ---------------------------------------------------------------------------
section_banner("Unrealized Performance by Asset Type")
gl1, gl2 = st.columns(2)
with gl1:
    gain_by_type = merged.groupby("AssetType", as_index=False)["UnrealizedGain"].sum()
    st.plotly_chart(ch.bar_chart(gain_by_type, "AssetType", "UnrealizedGain", title="Unrealized Gain / (Loss) by Asset Type", height=380),
                     use_container_width=True)
with gl2:
    st.plotly_chart(ch.histogram(merged, x="UnrealizedGainPct", title="Distribution of Position-Level Return %", height=380),
                     use_container_width=True)

# ---------------------------------------------------------------------------
# Asset-level explorer
# ---------------------------------------------------------------------------
section_banner("Asset Explorer")
search = st.text_input("Search by ticker or asset name")
explorer = merged.copy()
if search:
    mask = (
        explorer["TickerSymbol"].str.contains(search, case=False, na=False)
        | explorer["AssetName"].str.contains(search, case=False, na=False)
    )
    explorer = explorer[mask]

disp_cols = ["TickerSymbol", "AssetName", "AssetType", "Exchange", "PortfolioID", "Quantity",
             "PurchasePrice", "CurrentPrice", "MarketValue", "UnrealizedGainPct"]
disp = explorer[disp_cols].sort_values("MarketValue", ascending=False).head(500).copy()
disp["PurchasePrice"] = disp["PurchasePrice"].apply(lambda v: format_currency(v, compact=False))
disp["CurrentPrice"] = disp["CurrentPrice"].apply(lambda v: format_currency(v, compact=False))
disp["MarketValue"] = disp["MarketValue"].apply(format_currency)
disp["UnrealizedGainPct"] = disp["UnrealizedGainPct"].apply(format_pct)
disp.columns = ["Ticker", "Asset Name", "Type", "Exchange", "Portfolio ID", "Qty", "Purchase Px", "Current Px", "Market Value", "Return %"]
st.dataframe(disp, hide_index=True, use_container_width=True, height=420)
st.caption("Showing up to 500 matching positions, sorted by market value.")
