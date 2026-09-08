# -*- coding: utf-8 -*-
"""Advisor Performance — leaderboards, AUM trends, and book-of-business detail."""
import pandas as pd
import streamlit as st

import config as cfg
from utils import data_loader as dl
from utils import metrics as mx
from utils import charts as ch
from utils.styling import inject_global_css, page_header, section_banner, kpi_card, format_currency, format_pct, format_number

st.set_page_config(page_title="Advisor Performance", page_icon="👨‍💼", layout="wide")
inject_global_css()

with st.sidebar:
    st.markdown(f"# {cfg.APP_ICON} {cfg.FIRM_NAME}")
    st.divider()
    lookback = st.select_slider("Performance history window (months)", options=[6, 12, 18, 24], value=cfg.DEFAULT_LOOKBACK_MONTHS)
    if st.button("🔄 Refresh data", use_container_width=True):
        dl.clear_all_caches()
        st.rerun()

advisors_df = dl.load_advisors()
clients_df = dl.load_clients()
accounts_df = dl.load_accounts()
adv_metrics_df = dl.load_advisor_metrics(months_back=lookback)

page_header("Advisor Performance", "AUM, client returns, and book-of-business detail across the advisor team.")

# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------
f1, f2 = st.columns([1, 3])
with f1:
    status_filter = st.multiselect("Advisor status", options=sorted(advisors_df["Status"].dropna().unique()),
                                    default=["Active"])

filtered_advisors = advisors_df[advisors_df["Status"].isin(status_filter)] if status_filter else advisors_df

leaderboard = mx.advisor_leaderboard(adv_metrics_df, filtered_advisors)

# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------
k1, k2, k3, k4 = st.columns(4)
with k1:
    kpi_card("Advisors Shown", f"{filtered_advisors['AdvisorID'].nunique():,}")
with k2:
    kpi_card("Total AUM (latest mo.)", format_currency(leaderboard["TotalAUM"].sum()) if not leaderboard.empty else "—")
with k3:
    avg_ret = leaderboard["AverageClientReturn"].mean() if not leaderboard.empty else None
    kpi_card("Avg. Client Return", format_pct(avg_ret) if pd.notnull(avg_ret) else "—", positive=(avg_ret or 0) >= 0)
with k4:
    kpi_card("Total Clients Served", f"{int(leaderboard['NumberOfClients'].sum()):,}" if not leaderboard.empty else "—")

st.write("")

# ---------------------------------------------------------------------------
# Leaderboard table + AUM trend
# ---------------------------------------------------------------------------
section_banner("Advisor Leaderboard (Latest Month)")
if not leaderboard.empty:
    disp = leaderboard[["AdvisorName", "Status", "HireDate", "TotalAUM", "AverageClientReturn", "NumberOfClients"]].copy()
    disp["TotalAUM"] = disp["TotalAUM"].apply(format_currency)
    disp["AverageClientReturn"] = disp["AverageClientReturn"].apply(format_pct)
    disp.columns = ["Advisor", "Status", "Hire Date", "AUM", "Avg. Client Return", "# Clients"]
    st.dataframe(disp, hide_index=True, use_container_width=True, height=380)
else:
    st.info("No advisor metrics available for the current filters/window.")

section_banner("AUM Trend by Advisor")
if not adv_metrics_df.empty and not filtered_advisors.empty:
    trend_df = adv_metrics_df[adv_metrics_df["AdvisorID"].isin(filtered_advisors["AdvisorID"])].merge(
        filtered_advisors[["AdvisorID", "FirstName", "LastName"]], on="AdvisorID", how="left"
    )
    trend_df["AdvisorName"] = trend_df["FirstName"] + " " + trend_df["LastName"]

    top_n_names = leaderboard.head(8)["AdvisorName"].tolist() if not leaderboard.empty else []
    default_selection = top_n_names[:5]
    chosen = st.multiselect("Compare advisors", options=sorted(trend_df["AdvisorName"].dropna().unique()),
                             default=default_selection)
    plot_df = trend_df[trend_df["AdvisorName"].isin(chosen)] if chosen else trend_df[trend_df["AdvisorName"].isin(default_selection)]
    if not plot_df.empty:
        st.plotly_chart(
            ch.line_trend(plot_df, "CalculationDate", "TotalAUM", color="AdvisorName", title="Advisor AUM Over Time", height=420),
            use_container_width=True,
        )
    else:
        st.info("Select at least one advisor to plot.")
else:
    st.info("No trend data available.")

# ---------------------------------------------------------------------------
# Return distribution + client load scatter
# ---------------------------------------------------------------------------
section_banner("Risk / Return & Client Load")
sc1, sc2 = st.columns(2)
with sc1:
    if not leaderboard.empty:
        st.plotly_chart(
            ch.scatter_plot(
                leaderboard, x="NumberOfClients", y="AverageClientReturn", size="TotalAUM",
                hover_name="AdvisorName", color="AdvisorName",
                title="Client Load vs. Avg. Return (bubble = AUM)", height=420,
            ),
            use_container_width=True,
        )
    else:
        st.info("No data available.")
with sc2:
    if not leaderboard.empty:
        st.plotly_chart(
            ch.histogram(leaderboard, x="AverageClientReturn", title="Distribution of Advisor Returns", height=420),
            use_container_width=True,
        )
    else:
        st.info("No data available.")

# ---------------------------------------------------------------------------
# Drill-down: single advisor detail
# ---------------------------------------------------------------------------
section_banner("Advisor Drill-Down")
if not filtered_advisors.empty:
    adv_names = (filtered_advisors["FirstName"] + " " + filtered_advisors["LastName"] + " (ID " + filtered_advisors["AdvisorID"].astype(str) + ")")
    selection = st.selectbox("Select an advisor", options=adv_names.tolist())
    selected_id = int(selection.split("ID ")[-1].rstrip(")"))

    adv_row = filtered_advisors[filtered_advisors["AdvisorID"] == selected_id].iloc[0]
    adv_clients = clients_df[clients_df["AdvisorID"] == selected_id]
    adv_accounts = accounts_df[accounts_df["ClientID"].isin(adv_clients["ClientID"])]

    dcol1, dcol2, dcol3, dcol4 = st.columns(4)
    with dcol1:
        kpi_card("License #", adv_row["LicenseNumber"])
    with dcol2:
        kpi_card("Hire Date", str(adv_row["HireDate"]))
    with dcol3:
        kpi_card("Clients", f"{adv_clients['ClientID'].nunique():,}")
    with dcol4:
        kpi_card("Book AUM", format_currency(adv_accounts["Balance"].sum()))

    st.markdown("**Client Roster**")
    roster = adv_clients[["ClientID", "FirstName", "LastName", "City", "State", "RiskTolerance", "RegistrationDate"]].copy()
    roster.columns = ["Client ID", "First Name", "Last Name", "City", "Province", "Risk Tolerance", "Registered"]
    st.dataframe(roster, hide_index=True, use_container_width=True, height=320)
else:
    st.info("No advisors match the current filters.")
