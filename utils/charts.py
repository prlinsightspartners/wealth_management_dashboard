# -*- coding: utf-8 -*-
"""Reusable Plotly chart builders, pre-styled with the firm's theme."""
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

import config as cfg


def _base_layout(fig, title=None, height=380):
    fig.update_layout(
        template=cfg.PLOTLY_TEMPLATE,
        title=title,
        height=height,
        margin=dict(l=10, r=10, t=50 if title else 20, b=10),
        font=dict(family="Segoe UI, Arial", size=12, color=cfg.COLOR_PRIMARY),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    return fig


def line_trend(df: pd.DataFrame, x: str, y: str, title=None, color=None, height=380):
    fig = px.line(
        df, x=x, y=y, color=color, markers=True,
        color_discrete_sequence=cfg.CATEGORICAL_PALETTE,
    )
    fig.update_traces(line=dict(width=3))
    return _base_layout(fig, title, height)


def area_trend(df: pd.DataFrame, x: str, y: str, title=None, height=380):
    fig = px.area(df, x=x, y=y, color_discrete_sequence=[cfg.COLOR_PRIMARY])
    fig.update_traces(line=dict(width=2), fillcolor="rgba(11,37,69,0.15)")
    return _base_layout(fig, title, height)


def bar_chart(df: pd.DataFrame, x: str, y: str, title=None, color=None, horizontal=False, height=380, text_auto=True):
    if horizontal:
        fig = px.bar(df, x=y, y=x, orientation="h", color=color,
                     color_discrete_sequence=cfg.CATEGORICAL_PALETTE, text_auto=text_auto)
    else:
        fig = px.bar(df, x=x, y=y, color=color,
                     color_discrete_sequence=cfg.CATEGORICAL_PALETTE, text_auto=text_auto)
    return _base_layout(fig, title, height)


def donut_chart(df: pd.DataFrame, names: str, values: str, title=None, height=380):
    fig = px.pie(
        df, names=names, values=values, hole=0.55,
        color_discrete_sequence=cfg.CATEGORICAL_PALETTE,
    )
    fig.update_traces(textposition="outside", textinfo="percent+label")
    return _base_layout(fig, title, height)


def scatter_plot(df: pd.DataFrame, x: str, y: str, color=None, size=None, hover_name=None,
                  title=None, height=420):
    fig = px.scatter(
        df, x=x, y=y, color=color, size=size, hover_name=hover_name,
        color_discrete_sequence=cfg.CATEGORICAL_PALETTE,
    )
    fig.update_traces(marker=dict(line=dict(width=0.5, color="white")))
    return _base_layout(fig, title, height)


def histogram(df: pd.DataFrame, x: str, title=None, nbins=30, height=350):
    fig = px.histogram(df, x=x, nbins=nbins, color_discrete_sequence=[cfg.COLOR_PRIMARY])
    return _base_layout(fig, title, height)


def gauge_chart(value: float, title: str, max_value: float = 100, suffix: str = "%",
                 thresholds=(50, 80), height=260):
    low, high = thresholds
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            number={"suffix": suffix, "font": {"size": 28, "color": cfg.COLOR_PRIMARY}},
            title={"text": title, "font": {"size": 14}},
            gauge={
                "axis": {"range": [0, max_value]},
                "bar": {"color": cfg.COLOR_PRIMARY},
                "steps": [
                    {"range": [0, low], "color": "#E7ECF3"},
                    {"range": [low, high], "color": "#D7E2EE"},
                    {"range": [high, max_value], "color": "#C4D4E6"},
                ],
                "threshold": {
                    "line": {"color": cfg.COLOR_ACCENT, "width": 4},
                    "thickness": 0.8,
                    "value": value,
                },
            },
        )
    )
    fig.update_layout(height=height, margin=dict(l=20, r=20, t=40, b=10))
    return fig
