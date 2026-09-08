# -*- coding: utf-8 -*-
"""
Supabase connection layer.

Credentials are resolved in this order:
  1. Streamlit secrets (st.secrets) — used on Streamlit Community Cloud
     via .streamlit/secrets.toml
  2. Environment variables (loaded from a local .env file via python-dotenv)
     — used for local development

This lets the same codebase run unmodified locally and when deployed.
"""
import os
from typing import Optional, List, Dict, Any, Callable

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from supabase import create_client, Client

import config as cfg

load_dotenv()  # no-op in prod if no .env file is present


def _get_credential(key: str) -> Optional[str]:
    """Look up a credential from st.secrets first, then environment variables."""
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        # st.secrets raises if no secrets.toml exists at all — fall through to env vars
        pass
    return os.environ.get(key)


@st.cache_resource(show_spinner=False)
def get_client() -> Client:
    """Create (and cache) a single Supabase client for the app's lifetime."""
    url = _get_credential("SUPABASE_URL")
    key = _get_credential("SUPABASE_KEY")

    if not url or not key:
        st.error(
            "Supabase credentials are missing. Set **SUPABASE_URL** and **SUPABASE_KEY** "
            "either in a local `.env` file or in `.streamlit/secrets.toml` "
            "(see `.env.example` for the expected format)."
        )
        st.stop()

    return create_client(url, key)

def _table(table_name: str):
    """Return a query scoped to the application's Supabase schema."""
    return get_client().schema(cfg.SUPABASE_SCHEMA).table(table_name)


def fetch_all(
    table_name: str,
    columns: str = "*",
    page_size: int = 1000,
    order_by: Optional[str] = None,
    ascending: bool = True,
    filters: Optional[List[Callable[[Any], Any]]] = None,
    max_rows: Optional[int] = None,
) -> pd.DataFrame:
    """
    Fetch every row from a Supabase table, transparently paginating past the
    PostgREST default row cap.

    `filters` is a list of callables applied to the query builder, e.g.:
        filters=[lambda q: q.gte("TransactionDate", "2025-01-01")]

    `max_rows` optionally caps how many rows are pulled (useful for very large
    tables like Transactions when only a recent window is needed).
    """
    rows: List[Dict[str, Any]] = []
    start = 0

    while True:
        query = _table(table_name).select(columns)

        if filters:
            for f in filters:
                query = f(query)

        if order_by:
            query = query.order(order_by, desc=not ascending)

        end = start + page_size - 1
        query = query.range(start, end)

        response = query.execute()
        page = response.data or []
        rows.extend(page)

        if len(page) < page_size:
            break
        start += page_size

        if max_rows is not None and len(rows) >= max_rows:
            rows = rows[:max_rows]
            break

    return pd.DataFrame(rows)


def get_row_count(table_name: str, filters: Optional[List[Callable[[Any], Any]]] = None) -> int:
    """Return an exact row count for a table without pulling the data itself."""
    query = _table(table_name).select("*", count="exact", head=True)
    if filters:
        for f in filters:
            query = f(query)
    response = query.execute()
    return response.count or 0


def check_data_readiness() -> dict:
    """Check that the configured schema exposes usable dashboard tables."""
    result = {"errors": [], "warnings": [], "counts": {}}

    for table_name, columns in cfg.REQUIRED_COLUMNS.items():
        try:
            # This catches missing tables and columns, including empty tables.
            _table(table_name).select(",".join(columns)).limit(1).execute()
            count = get_row_count(table_name)
            result["counts"][table_name] = count
            if table_name in cfg.REQUIRED_NONEMPTY_TABLES and count == 0:
                result["errors"].append(f"{table_name} is empty.")
            elif count == 0:
                result["warnings"].append(
                    f"{table_name} is empty; related dashboard sections will have no data."
                )
        except Exception as exc:
            result["errors"].append(
                f"{table_name} is unavailable or missing required columns: {exc}"
            )

    return result
