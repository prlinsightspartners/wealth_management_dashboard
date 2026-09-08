# -*- coding: utf-8 -*-
"""Client Insights — demographics, engagement, and relationship health."""
import pandas as pd
import numpy as np
import streamlit as st

import config as cfg
from utils import data_loader as dl
from utils import metrics as mx
from utils import charts as ch
from utils.styling import inject_global_css, page_header, section_banner, kpi_card, format_currency

st.set_page_config(page_title="Client Insights", page_icon="🧑‍🤝‍🧑", layout="wide")
inject_global_css()

with st.sidebar:
    st.markdown(f"# {cfg.APP_ICON} {cfg.FIRM_NAME}")
    st.divider()
    lookback = st.select_slider("Interaction history window (months)", options=[6, 12, 18, 24], value=cfg.DEFAULT_LOOKBACK_MONTHS)
    if st.button("🔄 Refresh data", use_container_width=True):
        dl.clear_all_caches()
        st.rerun()

clients_df = dl.load_clients()
accounts_df = dl.load_accounts()
advisors_df = dl.load_advisors()
interactions_df = dl.load_interactions(months_back=lookback)

page_header("Client Insights", "Demographics, segmentation, and relationship engagement across the client base.")

# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------
provinces = sorted(clients_df["State"].dropna().unique())
risk_levels = [r for r in cfg.RISK_ORDER if r in clients_df["RiskTolerance"].unique()]

f1, f2 = st.columns(2)
with f1:
    prov_filter = st.multiselect("Province / Territory", options=provinces, default=provinces)
with f2:
    risk_filter = st.multiselect("Risk tolerance", options=risk_levels, default=risk_levels)

filtered_clients = clients_df[
    clients_df["State"].isin(prov_filter) & clients_df["RiskTolerance"].isin(risk_filter)
] if prov_filter and risk_filter else clients_df

client_aum = accounts_df.groupby("ClientID", as_index=False)["Balance"].sum().rename(columns={"Balance": "ClientAUM"})
filtered_clients = filtered_clients.merge(client_aum, on="ClientID", how="left")
filtered_clients["ClientAUM"] = filtered_clients["ClientAUM"].fillna(0)

# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------
k1, k2, k3, k4 = st.columns(4)
with k1:
    kpi_card("Clients Shown", f"{filtered_clients['ClientID'].nunique():,}")
with k2:
    kpi_card("Total AUM", format_currency(filtered_clients["ClientAUM"].sum()))
with k3:
    kpi_card("Avg. AUM / Client", format_currency(filtered_clients["ClientAUM"].mean()))
with k4:
    avg_age = filtered_clients["Age"].mean() if "Age" in filtered_clients.columns else np.nan
    kpi_card("Avg. Client Age", f"{avg_age:.0f}" if pd.notnull(avg_age) else "—")

st.write("")

# ---------------------------------------------------------------------------
# Demographics
# ---------------------------------------------------------------------------
section_banner("Demographics")
d1, d2, d3 = st.columns(3)
with d1:
    if "Age" in filtered_clients.columns:
        st.plotly_chart(ch.histogram(filtered_clients, x="Age", title="Age Distribution", height=340), use_container_width=True)
with d2:
    risk_dist = filtered_clients["RiskTolerance"].value_counts().rename_axis("RiskTolerance").reset_index(name="Count")
    st.plotly_chart(ch.donut_chart(risk_dist, "RiskTolerance", "Count", title="Risk Tolerance Mix", height=340), use_container_width=True)
with d3:
    prov_dist = filtered_clients["State"].value_counts().rename_axis("State").reset_index(name="Count")
    st.plotly_chart(ch.bar_chart(prov_dist, "State", "Count", title="Clients by Province", height=340), use_container_width=True)

# ---------------------------------------------------------------------------
# AUM segmentation (wealth tiers)
# ---------------------------------------------------------------------------
section_banner("Client Wealth Segmentation")
tier_bins = [0, 100_000, 500_000, 1_000_000, 5_000_000, np.inf]
tier_labels = ["<$100K", "$100K–$500K", "$500K–$1M", "$1M–$5M", "$5M+"]
filtered_clients["WealthTier"] = pd.cut(filtered_clients["ClientAUM"], bins=tier_bins, labels=tier_labels)
tier_summary = filtered_clients.groupby("WealthTier", as_index=False, observed=True).agg(
    Clients=("ClientID", "nunique"), TotalAUM=("ClientAUM", "sum")
)
tier_summary = tier_summary.set_index("WealthTier").reindex(tier_labels).reset_index()
tier_summary[["Clients", "TotalAUM"]] = tier_summary[["Clients", "TotalAUM"]].fillna(0)

seg1, seg2 = st.columns(2)
with seg1:
    st.plotly_chart(ch.bar_chart(tier_summary, "WealthTier", "Clients", title="Clients by Wealth Tier", height=360), use_container_width=True)
with seg2:
    st.plotly_chart(ch.bar_chart(tier_summary, "WealthTier", "TotalAUM", title="AUM by Wealth Tier", height=360), use_container_width=True)

# ---------------------------------------------------------------------------
# Growth & Engagement
# ---------------------------------------------------------------------------
section_banner("Growth & Engagement")
g1, g2 = st.columns(2)
with g1:
    growth = mx.client_growth(filtered_clients)
    st.plotly_chart(ch.line_trend(growth, "Month", "NewClients", title="New Clients per Month", height=380), use_container_width=True)
with g2:
    filt_interactions = interactions_df[interactions_df["ClientID"].isin(filtered_clients["ClientID"])]
    summary = mx.interaction_summary(filt_interactions)
    if not summary["monthly"].empty:
        st.plotly_chart(ch.line_trend(summary["monthly"], "Month", "Interactions", title="Client Interactions per Month", height=380),
                         use_container_width=True)
    else:
        st.info("No interaction data for current filters/window.")

# ---------------------------------------------------------------------------
# Interaction breakdown
# ---------------------------------------------------------------------------
section_banner("Interaction Type Breakdown & Follow-Ups")
i1, i2 = st.columns([2, 1])
with i1:
    if not summary["by_type"].empty:
        st.plotly_chart(ch.bar_chart(summary["by_type"], "InteractionType", "Count", title="Interactions by Type", horizontal=True, height=380),
                         use_container_width=True)
    else:
        st.info("No interaction data available.")
with i2:
    kpi_card("Total Interactions (window)", f"{summary['total']:,}")
    st.write("")
    kpi_card("Pending Follow-Ups", f"{summary['pending_followups']:,}")

# ---------------------------------------------------------------------------
# Client directory / drill-down
# ---------------------------------------------------------------------------
section_banner("Client Directory")
search = st.text_input("Search by last name or client ID")
directory = filtered_clients.copy()
if search:
    mask = directory["LastName"].str.contains(search, case=False, na=False) | directory["ClientID"].astype(str).str.contains(search)
    directory = directory[mask]

disp_cols = ["ClientID", "FirstName", "LastName", "City", "State", "Age", "RiskTolerance", "ClientAUM", "RegistrationDate"]
disp = directory[disp_cols].copy()
disp["ClientAUM"] = disp["ClientAUM"].apply(format_currency)
disp.columns = ["Client ID", "First Name", "Last Name", "City", "Province", "Age", "Risk Tolerance", "AUM", "Registered"]
st.dataframe(disp.sort_values("AUM", ascending=False), hide_index=True, use_container_width=True, height=400)
