# -*- coding: utf-8 -*-
"""
Executive Summary — Home page.

Run with:  streamlit run app.py
"""
from datetime import date

import pandas as pd
import streamlit as st

import config as cfg
from db.supabase_client import check_data_readiness
from utils import data_loader as dl
from utils import metrics as mx
from utils import charts as ch
from utils.styling import inject_global_css, page_header, section_banner, kpi_card, format_currency, format_pct, format_number

# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------
st.set_page_config(page_title=cfg.APP_TITLE, page_icon=cfg.APP_ICON, layout="wide")
inject_global_css()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"# {cfg.APP_ICON} {cfg.FIRM_NAME}")
    st.caption("Institutional Wealth & Asset Management")
    st.divider()
    st.markdown("### Navigation")
    st.caption("Use the pages above to drill into Advisors, Portfolios, Clients, Asset Allocation, and Transactions.")
    st.divider()
    lookback = st.select_slider(
        "Performance history window (months)",
        options=[6, 12, 18, 24],
        value=cfg.DEFAULT_LOOKBACK_MONTHS,
        help="Controls how much monthly performance history is pulled for AUM trends and leaderboards.",
    )
    if st.button("🔄 Refresh data from Supabase", use_container_width=True):
        dl.clear_all_caches()
        st.rerun()
    st.divider()
    st.caption(f"Data as of {date.today():%B %d, %Y}")

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
readiness = check_data_readiness()
if readiness["errors"]:
    st.error("Supabase data is not ready for this dashboard.")
    for error in readiness["errors"]:
        st.error(error)
    st.info(
        f"The app is querying the `{cfg.SUPABASE_SCHEMA}` schema. "
        "Check SUPABASE_URL and SUPABASE_KEY if this is unexpected."
    )
    st.stop()

for warning in readiness["warnings"]:
    st.warning(warning)

advisors_df = dl.load_advisors()
clients_df = dl.load_clients()
accounts_df = dl.load_accounts()
portfolios_df = dl.load_portfolios()
assets_df = dl.load_assets()
holdings_df = dl.load_holdings()
interactions_df = dl.load_interactions(months_back=lookback)
pf_metrics_df = dl.load_portfolio_metrics(months_back=lookback)
adv_metrics_df = dl.load_advisor_metrics(months_back=lookback)

if clients_df.empty or advisors_df.empty:
    st.warning(
        "No data returned from Supabase yet. Confirm your tables are populated and that "
        "SUPABASE_URL / SUPABASE_KEY are set correctly."
    )
    st.stop()

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
page_header(
    "Executive Summary",
    f"Firm-wide overview across {advisors_df['AdvisorID'].nunique():,} advisors, "
    f"{clients_df['ClientID'].nunique():,} clients, and {portfolios_df['PortfolioID'].nunique():,} portfolios.",
)

# ---------------------------------------------------------------------------
# KPI Row
# ---------------------------------------------------------------------------
kpis = mx.firm_kpis(clients_df, advisors_df, accounts_df, portfolios_df, pf_metrics_df, adv_metrics_df)

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    kpi_card("Total AUM", format_currency(kpis["total_aum"]))
with c2:
    kpi_card("Active Clients", f"{kpis['active_clients']:,}")
with c3:
    kpi_card("Active Advisors", f"{kpis['active_advisors']:,}")
with c4:
    avg_ret = kpis["avg_client_return"]
    kpi_card(
        "Avg. Client Return (latest mo.)",
        format_pct(avg_ret) if pd.notnull(avg_ret) else "—",
        positive=(avg_ret or 0) >= 0,
    )
with c5:
    kpi_card("Avg. Portfolio Sharpe", format_number(kpis["avg_sharpe"]))

c6, c7, c8, c9, c10 = st.columns(5)
with c6:
    kpi_card("Total Accounts", f"{kpis['total_accounts']:,}")
with c7:
    kpi_card("Total Portfolios", f"{kpis['total_portfolios']:,}")
with c8:
    kpi_card("Accounts / Client (avg)", f"{kpis['avg_accounts_per_client']:.1f}")
with c9:
    kpi_card("AUM / Advisor (avg)", format_currency(kpis["avg_aum_per_advisor"]))
with c10:
    interaction_stats = mx.interaction_summary(interactions_df)
    kpi_card("Client Touchpoints (window)", f"{interaction_stats['total']:,}")

st.write("")

# ---------------------------------------------------------------------------
# AUM Trend + Asset Allocation
# ---------------------------------------------------------------------------
section_banner("Assets Under Management")
left, right = st.columns([2, 1])

with left:
    trend = mx.aum_trend(pf_metrics_df)
    if not trend.empty:
        st.plotly_chart(
            ch.area_trend(trend, "CalculationDate", "AUM", title="Firm-Wide AUM Trend"),
            use_container_width=True,
        )
    else:
        st.info("No AUM history available for the selected window.")

with right:
    alloc = mx.asset_allocation(holdings_df, assets_df)
    if not alloc.empty:
        st.plotly_chart(
            ch.donut_chart(alloc, "AssetType", "MarketValue", title="Allocation by Asset Type"),
            use_container_width=True,
        )
    else:
        st.info("No holdings data available.")

# ---------------------------------------------------------------------------
# Advisor & Portfolio Leaderboards
# ---------------------------------------------------------------------------
section_banner("Top Performers")
adv_col, pf_col = st.columns(2)

with adv_col:
    st.markdown("**Top 10 Advisors by AUM**")
    leaderboard = mx.advisor_leaderboard(adv_metrics_df, advisors_df)
    if not leaderboard.empty:
        top10 = leaderboard.head(10)[["AdvisorName", "TotalAUM", "AverageClientReturn", "NumberOfClients"]].copy()
        top10["TotalAUM"] = top10["TotalAUM"].apply(format_currency)
        top10["AverageClientReturn"] = top10["AverageClientReturn"].apply(format_pct)
        top10.columns = ["Advisor", "AUM", "Avg. Client Return", "# Clients"]
        st.dataframe(top10, hide_index=True, use_container_width=True)
    else:
        st.info("No advisor performance data available for the selected window.")

with pf_col:
    st.markdown("**Top 10 Portfolios by Return (latest month)**")
    pf_leaderboard = mx.portfolio_leaderboard(pf_metrics_df, portfolios_df)
    if not pf_leaderboard.empty:
        top10_pf = pf_leaderboard.head(10)[["PortfolioName", "InvestmentStrategy", "AUM", "ReturnAbsolute", "SharpeRatio"]].copy()
        top10_pf["AUM"] = top10_pf["AUM"].apply(format_currency)
        top10_pf["ReturnAbsolute"] = top10_pf["ReturnAbsolute"].apply(format_pct)
        top10_pf.columns = ["Portfolio", "Strategy", "AUM", "Return", "Sharpe"]
        st.dataframe(top10_pf, hide_index=True, use_container_width=True)
    else:
        st.info("No portfolio performance data available for the selected window.")

# ---------------------------------------------------------------------------
# Risk / Client Base Composition
# ---------------------------------------------------------------------------
section_banner("Client Base Composition")
risk_col, prov_col, growth_col = st.columns(3)

with risk_col:
    risk_dist = mx.risk_tolerance_distribution(clients_df)
    st.plotly_chart(
        ch.donut_chart(risk_dist, "RiskTolerance", "Count", title="Risk Tolerance Mix", height=340),
        use_container_width=True,
    )

with prov_col:
    prov_dist = mx.province_distribution(clients_df, accounts_df)
    st.plotly_chart(
        ch.bar_chart(prov_dist.head(8), "State", "Clients", title="Clients by Province (Top 8)", height=340),
        use_container_width=True,
    )

with growth_col:
    growth = mx.client_growth(clients_df)
    st.plotly_chart(
        ch.line_trend(growth, "Month", "CumulativeClients", title="Cumulative Client Growth", height=340),
        use_container_width=True,
    )

# ---------------------------------------------------------------------------
# Attention Needed — operational alerts
# ---------------------------------------------------------------------------
section_banner("Attention Needed")
alert_col1, alert_col2, alert_col3 = st.columns(3)

with alert_col1:
    st.markdown("**Underperforming Portfolios (negative Sharpe, latest mo.)**")
    if not pf_leaderboard.empty:
        underperf = pf_leaderboard[pf_leaderboard["SharpeRatio"] < 0].sort_values("SharpeRatio").head(8)
        if not underperf.empty:
            disp = underperf[["PortfolioName", "InvestmentStrategy", "SharpeRatio", "ReturnAbsolute"]].copy()
            disp["ReturnAbsolute"] = disp["ReturnAbsolute"].apply(format_pct)
            disp.columns = ["Portfolio", "Strategy", "Sharpe", "Return"]
            st.dataframe(disp, hide_index=True, use_container_width=True)
        else:
            st.success("No portfolios currently flagged.")
    else:
        st.info("No data for the selected window.")

with alert_col2:
    st.markdown("**Portfolios Not Rebalanced in 180+ Days**")
    if not portfolios_df.empty:
        stale_cutoff = pd.Timestamp(date.today()) - pd.Timedelta(days=180)
        pf_copy = portfolios_df.copy()
        pf_copy["LastRebalanceDate"] = pd.to_datetime(pf_copy["LastRebalanceDate"])
        stale = pf_copy[pf_copy["LastRebalanceDate"] < stale_cutoff].sort_values("LastRebalanceDate")
        st.metric("Portfolios overdue for rebalance", f"{len(stale):,}")
        if not stale.empty:
            st.dataframe(
                stale[["PortfolioName", "InvestmentStrategy", "LastRebalanceDate"]].head(8),
                hide_index=True, use_container_width=True,
            )
    else:
        st.info("No portfolio data available.")

with alert_col3:
    st.markdown("**Client Interactions Pending Follow-Up**")
    if not interactions_df.empty and "FollowUpDate" in interactions_df.columns:
        pending = interactions_df[
            interactions_df["FollowUpDate"].notna()
            & (pd.to_datetime(interactions_df["FollowUpDate"]) >= pd.Timestamp(date.today()))
        ].sort_values("FollowUpDate")
        st.metric("Upcoming follow-ups", f"{len(pending):,}")
        if not pending.empty:
            disp = pending[["ClientID", "InteractionType", "FollowUpDate"]].head(8)
            st.dataframe(disp, hide_index=True, use_container_width=True)
    else:
        st.info("No interaction data available for the selected window.")

st.divider()
st.caption(
    "Data sourced live from Supabase. Use the sidebar to widen the performance history window or "
    "refresh cached data. Detailed breakdowns are available via the pages in the left navigation."
)
