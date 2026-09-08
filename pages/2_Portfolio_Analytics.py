# -*- coding: utf-8 -*-
"""Portfolio Analytics — strategy performance, risk metrics, and rebalancing status."""
import pandas as pd
import streamlit as st

import config as cfg
from utils import data_loader as dl
from utils import metrics as mx
from utils import charts as ch
from utils.styling import inject_global_css, page_header, section_banner, kpi_card, format_currency, format_pct, format_number

st.set_page_config(page_title="Portfolio Analytics", page_icon="📈", layout="wide")
inject_global_css()

with st.sidebar:
    st.markdown(f"# {cfg.APP_ICON} {cfg.FIRM_NAME}")
    st.divider()
    lookback = st.select_slider("Performance history window (months)", options=[6, 12, 18, 24], value=cfg.DEFAULT_LOOKBACK_MONTHS)
    if st.button("🔄 Refresh data", use_container_width=True):
        dl.clear_all_caches()
        st.rerun()

portfolios_df = dl.load_portfolios()
accounts_df = dl.load_accounts()
clients_df = dl.load_clients()
pf_metrics_df = dl.load_portfolio_metrics(months_back=lookback)

page_header("Portfolio Analytics", "Performance, risk, and strategy mix across every managed portfolio.")

# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------
strategies = sorted(portfolios_df["InvestmentStrategy"].dropna().unique())
f1, f2 = st.columns([2, 1])
with f1:
    strategy_filter = st.multiselect("Investment strategy", options=strategies, default=strategies)
with f2:
    min_aum = st.number_input("Minimum AUM filter ($)", min_value=0, value=0, step=10000)

filtered_portfolios = portfolios_df[portfolios_df["InvestmentStrategy"].isin(strategy_filter)] if strategy_filter else portfolios_df
pf_leaderboard = mx.portfolio_leaderboard(pf_metrics_df, filtered_portfolios)
if not pf_leaderboard.empty and min_aum:
    pf_leaderboard = pf_leaderboard[pf_leaderboard["AUM"] >= min_aum]

# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------
k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    kpi_card("Portfolios Shown", f"{pf_leaderboard['PortfolioID'].nunique():,}" if not pf_leaderboard.empty else "0")
with k2:
    kpi_card("Total AUM", format_currency(pf_leaderboard["AUM"].sum()) if not pf_leaderboard.empty else "—")
with k3:
    avg_ret = pf_leaderboard["ReturnAbsolute"].mean() if not pf_leaderboard.empty else None
    kpi_card("Avg. Return", format_pct(avg_ret) if pd.notnull(avg_ret) else "—", positive=(avg_ret or 0) >= 0)
with k4:
    kpi_card("Avg. Sharpe Ratio", format_number(pf_leaderboard["SharpeRatio"].mean()) if not pf_leaderboard.empty else "—")
with k5:
    kpi_card("Avg. Beta", format_number(pf_leaderboard["Beta"].mean()) if not pf_leaderboard.empty else "—")

st.write("")

# ---------------------------------------------------------------------------
# Strategy breakdown
# ---------------------------------------------------------------------------
section_banner("Performance by Investment Strategy")
strat = mx.strategy_breakdown(filtered_portfolios, pf_metrics_df)
s1, s2 = st.columns(2)
with s1:
    if not strat.empty:
        st.plotly_chart(ch.bar_chart(strat, "InvestmentStrategy", "AUM", title="AUM by Strategy", horizontal=True, height=420),
                         use_container_width=True)
    else:
        st.info("No strategy data available.")
with s2:
    if not strat.empty:
        st.plotly_chart(ch.bar_chart(strat, "InvestmentStrategy", "AvgReturn", title="Avg. Return by Strategy", horizontal=True, height=420),
                         use_container_width=True)
    else:
        st.info("No strategy data available.")

# ---------------------------------------------------------------------------
# Risk / Return scatter + Sharpe distribution
# ---------------------------------------------------------------------------
section_banner("Risk-Adjusted Performance")
r1, r2 = st.columns(2)
with r1:
    if not pf_leaderboard.empty:
        st.plotly_chart(
            ch.scatter_plot(
                pf_leaderboard, x="Beta", y="ReturnAbsolute", size="AUM", color="InvestmentStrategy",
                hover_name="PortfolioName", title="Return vs. Beta (bubble = AUM)", height=440,
            ),
            use_container_width=True,
        )
    else:
        st.info("No data available.")
with r2:
    if not pf_leaderboard.empty:
        st.plotly_chart(
            ch.histogram(pf_leaderboard, x="SharpeRatio", title="Sharpe Ratio Distribution", height=440),
            use_container_width=True,
        )
    else:
        st.info("No data available.")

# ---------------------------------------------------------------------------
# AUM trend for selected strategies
# ---------------------------------------------------------------------------
section_banner("AUM Trend by Strategy")
if not pf_metrics_df.empty:
    trend_src = pf_metrics_df.merge(portfolios_df[["PortfolioID", "InvestmentStrategy"]], on="PortfolioID", how="left")
    trend_src = trend_src[trend_src["InvestmentStrategy"].isin(strategy_filter)] if strategy_filter else trend_src
    trend_grouped = trend_src.groupby(["CalculationDate", "InvestmentStrategy"], as_index=False)["AUM"].sum()
    if not trend_grouped.empty:
        st.plotly_chart(
            ch.line_trend(trend_grouped, "CalculationDate", "AUM", color="InvestmentStrategy", title=None, height=420),
            use_container_width=True,
        )
    else:
        st.info("No AUM trend data for current filters.")
else:
    st.info("No performance history available.")

# ---------------------------------------------------------------------------
# Top / Bottom performers table
# ---------------------------------------------------------------------------
section_banner("Top & Bottom Performing Portfolios (Latest Month)")
t1, t2 = st.columns(2)
with t1:
    st.markdown("**Top 10 by Return**")
    if not pf_leaderboard.empty:
        top10 = pf_leaderboard.sort_values("ReturnAbsolute", ascending=False).head(10)
        disp = top10[["PortfolioName", "InvestmentStrategy", "AUM", "ReturnAbsolute", "SharpeRatio"]].copy()
        disp["AUM"] = disp["AUM"].apply(format_currency)
        disp["ReturnAbsolute"] = disp["ReturnAbsolute"].apply(format_pct)
        disp.columns = ["Portfolio", "Strategy", "AUM", "Return", "Sharpe"]
        st.dataframe(disp, hide_index=True, use_container_width=True)
    else:
        st.info("No data available.")
with t2:
    st.markdown("**Bottom 10 by Return**")
    if not pf_leaderboard.empty:
        bottom10 = pf_leaderboard.sort_values("ReturnAbsolute", ascending=True).head(10)
        disp = bottom10[["PortfolioName", "InvestmentStrategy", "AUM", "ReturnAbsolute", "SharpeRatio"]].copy()
        disp["AUM"] = disp["AUM"].apply(format_currency)
        disp["ReturnAbsolute"] = disp["ReturnAbsolute"].apply(format_pct)
        disp.columns = ["Portfolio", "Strategy", "AUM", "Return", "Sharpe"]
        st.dataframe(disp, hide_index=True, use_container_width=True)
    else:
        st.info("No data available.")

# ---------------------------------------------------------------------------
# Rebalancing status
# ---------------------------------------------------------------------------
section_banner("Rebalancing Cadence")
if not filtered_portfolios.empty:
    pf_copy = filtered_portfolios.copy()
    pf_copy["LastRebalanceDate"] = pd.to_datetime(pf_copy["LastRebalanceDate"])
    pf_copy["DaysSinceRebalance"] = (pd.Timestamp.today() - pf_copy["LastRebalanceDate"]).dt.days
    bins = [0, 90, 180, 365, 10000]
    labels = ["0-90 days", "91-180 days", "181-365 days", "365+ days"]
    pf_copy["RebalanceBucket"] = pd.cut(pf_copy["DaysSinceRebalance"], bins=bins, labels=labels)
    bucket_counts = pf_copy["RebalanceBucket"].value_counts().reindex(labels).reset_index()
    bucket_counts.columns = ["RebalanceBucket", "Count"]
    st.plotly_chart(
        ch.bar_chart(bucket_counts, "RebalanceBucket", "Count", title="Portfolios by Time Since Last Rebalance", height=340),
        use_container_width=True,
    )
else:
    st.info("No portfolio data available.")
