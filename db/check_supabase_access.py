"""Diagnose Supabase credentials and access to the dashboard schema.

Run from the project root:
    python db/check_supabase_access.py

Optional arguments:
    python db/check_supabase_access.py --schema asset_management
    python db/check_supabase_access.py --table Clients

The script reads SUPABASE_URL and SUPABASE_KEY from Streamlit secrets,
environment variables, or a project-root .env file. It never prints the key.
"""
import argparse
import os
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError
from supabase import create_client

# Allow this script to be run directly from the project root or from db/.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config as cfg

load_dotenv(PROJECT_ROOT / ".env")


def _error_text(exc: Exception) -> str:
    message = str(exc).strip().replace("\n", " ")
    return message or exc.__class__.__name__


def _get_credential(key: str) -> Optional[str]:
    """Look up a credential in Streamlit secrets, then the environment."""
    try:
        value = st.secrets.get(key)
    except StreamlitSecretNotFoundError:
        value = None
    return value or os.environ.get(key)


def _diagnostic_hint(exc: Exception) -> str:
    message = _error_text(exc)
    if "Invalid schema" in message or "PGRST106" in message:
        return " Add asset_management to Supabase API exposed schemas, then retry."
    if "Could not find the table" in message or "PGRST205" in message:
        return " Check the exact case of the table name and reload the PostgREST schema cache."
        if "permission denied for schema" in message.lower():
            return " Grant USAGE on asset_management to the API role, expose the schema in Supabase API settings, then reload the schema cache."
        if "permission" in message.lower() or "42501" in message:
            return " Grant the configured API role SELECT access to this schema/table and check its RLS policy."
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check Supabase credentials and dashboard table access."
    )
    parser.add_argument(
        "--schema",
        default=cfg.SUPABASE_SCHEMA,
        help=f"Supabase schema to test (default: {cfg.SUPABASE_SCHEMA}).",
    )
    parser.add_argument(
        "--table",
        help="Check only one configured table instead of all dashboard tables.",
    )
    args = parser.parse_args()

    url = _get_credential("SUPABASE_URL")
    key = _get_credential("SUPABASE_KEY")
    if not url or not key:
        print(
            "FAIL: SUPABASE_URL and SUPABASE_KEY must be set in Streamlit secrets, "
            "the environment, or the project-root .env file."
        )
        return 1

    try:
        client = create_client(url, key)
    except Exception as exc:
        print(f"FAIL: Supabase client could not be created: {_error_text(exc)}")
        return 1

    print(f"Supabase URL: {url}")
    print(f"Schema: {args.schema}")
    print("Credentials: loaded")

    tables = cfg.REQUIRED_COLUMNS
    if args.table:
        if args.table not in tables:
            print(f"FAIL: {args.table!r} is not one of the configured dashboard tables.")
            return 1
        tables = {args.table: cfg.REQUIRED_COLUMNS[args.table]}

    failures = 0
    for table_name, columns in tables.items():
        try:
            response = (
                client.schema(args.schema)
                .table(table_name)
                .select(",".join(columns), count="exact")
                .limit(1)
                .execute()
            )
            count = response.count if response.count is not None else "unknown"
            print(f"PASS: {table_name} is accessible ({count} rows; required columns found)")
        except Exception as exc:
            failures += 1
            print(f"FAIL: {table_name}: {_error_text(exc)}{_diagnostic_hint(exc)}")

    if failures:
        print(f"\nResult: {failures} table check(s) failed.")
        print("Check the schema name, table names, column names, and SELECT/RLS permissions.")
        return 1

    print(f"\nResult: all {len(tables)} table check(s) passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
