# -*- coding: utf-8 -*-
"""Shared visual styling — custom CSS and small UI component helpers."""
import streamlit as st
import config as cfg


def inject_global_css():
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {cfg.COLOR_BACKGROUND};
        }}
        /* Sidebar */
        section[data-testid="stSidebar"] {{
            background-color: {cfg.COLOR_PRIMARY};
        }}
        section[data-testid="stSidebar"] * {{
            color: #F5F7FA !important;
        }}
        section[data-testid="stSidebar"] hr {{
            border-color: rgba(255,255,255,0.15);
        }}

        /* Headings */
        h1, h2, h3 {{
            color: {cfg.COLOR_PRIMARY};
            font-family: 'Georgia', 'Segoe UI', serif;
        }}

        /* KPI cards */
        .kpi-card {{
            background-color: {cfg.COLOR_CARD_BG};
            border-radius: 10px;
            padding: 18px 20px;
            box-shadow: 0 1px 4px rgba(11, 37, 69, 0.12);
            border-left: 5px solid {cfg.COLOR_ACCENT};
            height: 100%;
        }}
        .kpi-label {{
            font-size: 0.80rem;
            font-weight: 600;
            color: {cfg.COLOR_NEUTRAL};
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 4px;
        }}
        .kpi-value {{
            font-size: 1.65rem;
            font-weight: 700;
            color: {cfg.COLOR_PRIMARY};
        }}
        .kpi-delta-pos {{
            color: {cfg.COLOR_POSITIVE};
            font-weight: 600;
            font-size: 0.85rem;
        }}
        .kpi-delta-neg {{
            color: {cfg.COLOR_NEGATIVE};
            font-weight: 600;
            font-size: 0.85rem;
        }}

        .section-banner {{
            background-color: {cfg.COLOR_PRIMARY};
            color: white;
            padding: 10px 16px;
            border-radius: 6px;
            margin: 18px 0 10px 0;
            font-weight: 600;
            letter-spacing: 0.02em;
        }}

        /* DataFrames */
        div[data-testid="stDataFrame"] {{
            border: 1px solid #E3E7EE;
            border-radius: 8px;
        }}

        footer {{visibility: hidden;}}
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str = ""):
    st.markdown(f"## {title}")
    if subtitle:
        st.caption(subtitle)
    st.divider()


def section_banner(text: str):
    st.markdown(f'<div class="section-banner">{text}</div>', unsafe_allow_html=True)


def kpi_card(label: str, value: str, delta: str = None, positive: bool = True):
    delta_html = ""
    if delta:
        cls = "kpi-delta-pos" if positive else "kpi-delta-neg"
        arrow = "▲" if positive else "▼"
        delta_html = f'<div class="{cls}">{arrow} {delta}</div>'
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_currency(value: float, compact: bool = True) -> str:
    if value is None or value != value:  # NaN check
        return "—"
    sign = "-" if value < 0 else ""
    value = abs(value)
    if compact:
        if value >= 1_000_000_000:
            return f"{sign}${value / 1_000_000_000:,.2f}B"
        if value >= 1_000_000:
            return f"{sign}${value / 1_000_000:,.2f}M"
        if value >= 1_000:
            return f"{sign}${value / 1_000:,.1f}K"
    return f"{sign}${value:,.2f}"


def format_pct(value: float, decimals: int = 2) -> str:
    """Formats a fractional return (e.g. 0.0314) as a percentage string."""
    if value is None or value != value:
        return "—"
    return f"{value * 100:.{decimals}f}%"


def format_number(value: float, decimals: int = 2) -> str:
    if value is None or value != value:
        return "—"
    return f"{value:,.{decimals}f}"
