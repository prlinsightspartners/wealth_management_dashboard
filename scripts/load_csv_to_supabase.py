# -*- coding: utf-8 -*-
"""
scripts/load_csv_to_supabase.py

    Optional loader for pushing synthetic CSV exports into existing Supabase
    tables. The Streamlit app validates and reads the existing data directly;
    this script is only needed when refreshing that data.

Usage
-----
    python scripts/load_csv_to_supabase.py --data-dir ./data

Environment variables required (or set them in a .env file at project root):
    SUPABASE_URL
    SUPABASE_KEY   (use the service_role key for this script — it needs
                    insert privileges; the anon key used by the Streamlit
                    app only needs read access)

Notes
-----
- Tables are loaded in dependency order (parents before children) so
  foreign keys resolve correctly.
- Data is upserted in batches on the primary key column, so the script is
  safe to re-run (e.g. after regenerating the synthetic data).
- NaN / NaT values are converted to None so they serialize to SQL NULL.
"""
import argparse
import math
import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

import config as cfg

load_dotenv()

# (csv filename without extension, Supabase table name, primary key column)
LOAD_ORDER = [
    ("Investmentadvisors", "Investmentadvisors", "AdvisorID"),
    ("Clients", "Clients", "ClientID"),
    ("Accounts", "Accounts", "AccountID"),
    ("Portfolios", "Portfolios", "PortfolioID"),
    ("Assets", "Assets", "AssetID"),
    ("PortfolioHoldings", "Portfolioholdings", "HoldingID"),
    ("Transactions", "Transactions", "TransactionID"),
    ("ClientInteractions", "Clientinteractions", "InteractionID"),
    ("PortfolioPerformanceMetrics", "Portfolioperformancemetrics", "MetricID"),
    ("AdvisorPerformanceMetrics", "Advisorperformancemetrics", "MetricID"),
]

DATE_COLUMNS_BY_TABLE = {
    "Investmentadvisors": ["HireDate"],
    "Clients": ["DateOfBirth", "RegistrationDate"],
    "Accounts": ["OpeningDate"],
    "Portfolios": ["CreationDate", "LastRebalanceDate"],
    "Portfolioholdings": ["PurchaseDate"],
    "Clientinteractions": ["FollowUpDate"],
    "Portfolioperformancemetrics": ["CalculationDate"],
    "Advisorperformancemetrics": ["CalculationDate"],
}
DATETIME_COLUMNS_BY_TABLE = {
    "Portfolioholdings": ["LastUpdated"],
    "Transactions": ["TransactionDate"],
    "Clientinteractions": ["InteractionDate"],
    "Portfolioperformancemetrics": ["CreatedAt", "UpdatedAt"],
    "Advisorperformancemetrics": ["CreatedAt", "UpdatedAt"],
}


def clean_records(df: pd.DataFrame, table: str) -> list:
    df = df.copy()
    for col in DATE_COLUMNS_BY_TABLE.get(table, []):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d")
    for col in DATETIME_COLUMNS_BY_TABLE.get(table, []):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%dT%H:%M:%S")

    records = df.to_dict(orient="records")
    for rec in records:
        for k, v in rec.items():
            if isinstance(v, float) and math.isnan(v):
                rec[k] = None
            elif v is pd.NaT:
                rec[k] = None
            elif isinstance(v, str) and v.lower() == "nat":
                rec[k] = None
    return records


def batched(iterable, batch_size):
    for i in range(0, len(iterable), batch_size):
        yield iterable[i : i + batch_size]


def main():
    parser = argparse.ArgumentParser(description="Load synthetic CSVs into Supabase.")
    parser.add_argument("--data-dir", default="./data", help="Folder containing the CSV files.")
    parser.add_argument("--batch-size", type=int, default=500, help="Rows per upsert batch.")
    parser.add_argument("--tables", nargs="*", default=None,
                         help="Optional subset of table names to load (defaults to all).")
    args = parser.parse_args()

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        sys.exit("ERROR: SUPABASE_URL and SUPABASE_KEY must be set (env vars or .env file).")

    client = create_client(url, key)
    data_dir = Path(args.data_dir)

    for csv_name, table_name, pk in LOAD_ORDER:
        if args.tables and table_name not in args.tables:
            continue

        csv_path = data_dir / f"{csv_name}.csv"
        if not csv_path.exists():
            print(f"  [skip] {csv_path} not found.")
            continue

        print(f"Loading {csv_path.name} -> \"{table_name}\" ...")
        df = pd.read_csv(csv_path)
        records = clean_records(df, table_name)

        total = len(records)
        for i, batch in enumerate(batched(records, args.batch_size), start=1):
            client.schema(cfg.SUPABASE_SCHEMA).table(table_name).upsert(
                batch, on_conflict=pk
            ).execute()
            done = min(i * args.batch_size, total)
            print(f"    ...{done}/{total} rows", end="\r")
        print(f"    done: {total}/{total} rows.        ")

    print("\nAll requested tables loaded.")


if __name__ == "__main__":
    main()
