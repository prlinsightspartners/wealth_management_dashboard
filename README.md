# Wealth & Asset Management — Executive Dashboard

A multi-page Streamlit dashboard for a Canadian institutional wealth & asset
management firm, reading live from Supabase. Built on the 10 core tables:
`Investmentadvisors`, `Clients`, `Accounts`, `Portfolios`, `Assets`,
`Portfolioholdings`, `Transactions`, `Clientinteractions`,
`Portfolioperformancemetrics`, and `Advisorperformancemetrics`.

## What's included

| Page | Focus |
|---|---|
| `app.py` (Home) | Executive Summary — firm-wide AUM, KPIs, leaderboards, alerts |
| `1_👨‍💼_Advisor_Performance.py` | Advisor leaderboard, AUM trends, book-of-business drill-down |
| `2_📈_Portfolio_Analytics.py` | Strategy performance, Sharpe/Beta/Alpha, rebalancing status |
| `3_🧑‍🤝‍🧑_Client_Insights.py` | Demographics, wealth segmentation, engagement trends |
| `4_💰_Asset_Allocation.py` | Allocation mix, concentration risk, top holdings |
| `5_💳_Transactions_Activity.py` | Trading volume, commission revenue, activity logs |

## Project layout

```
wealth-dashboard/
├── app.py                          # Home page (Executive Summary)
├── config.py                       # Schema, table names, required columns, settings
├── requirements.txt
├── .env.example                    # Copy to .env for local dev
├── .gitignore
├── README.md
├── db/
│   ├── supabase_client.py           # Connection, readiness check, paginated fetch
│   └── check_supabase_access.py     # Standalone credentials/schema diagnostic
├── utils/
│   ├── data_loader.py              # Cached per-table loaders (st.cache_data)
│   ├── metrics.py                  # KPI / aggregate computation logic
│   ├── charts.py                   # Reusable Plotly chart builders
│   └── styling.py                  # Custom CSS + KPI card component
├── pages/                          # Streamlit auto-discovers these for the sidebar nav
│   ├── 1_👨‍💼_Advisor_Performance.py
│   ├── 2_📈_Portfolio_Analytics.py
│   ├── 3_🧑‍🤝‍🧑_Client_Insights.py
│   ├── 4_💰_Asset_Allocation.py
│   └── 5_💳_Transactions_Activity.py
├── sql/
│   └── schema.sql                  # Reference schema for a new database
├── scripts/
│   └── load_csv_to_supabase.py     # Optional CSV -> Supabase refresh utility
└── .streamlit/
    ├── config.toml                 # Theme
    └── secrets.toml.example        # Copy to secrets.toml for Streamlit Cloud
```

## 1. Connect the existing Supabase database

The application expects the existing tables and data in the Supabase
`asset_management` schema. It does not create or alter tables at startup.

1. Grab the credentials from **Project Settings > API**:
  - `Project URL` → `SUPABASE_URL`
  - `anon` `public` key → `SUPABASE_KEY` (used by the Streamlit app; read-only)
2. Confirm that the anon key has `SELECT` access to the `asset_management`
  schema and its tables.

The ten expected tables are `Investmentadvisors`, `Clients`, `Accounts`,
`Portfolios`, `Assets`, `Portfolioholdings`, `Transactions`,
`Clientinteractions`, `Portfolioperformancemetrics`, and
`Advisorperformancemetrics`.

The `sql/schema.sql` file is retained as a reference for the expected table
structure. Do not run it against the existing database unless you are setting
up a separate database and have reviewed its schema and policies.

If the existing database still uses the previous multi-word table names, run
`sql/rename_tables.sql` in the `asset_management` schema before starting the
updated app.

## 2. Configure the app's credentials

For local development, create a `.env` file with the anon key:

```bash
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your-anon-public-api-key
```

For Streamlit Community Cloud, instead copy `.streamlit/secrets.toml.example`
to `.streamlit/secrets.toml` locally to test, then set the same two keys
under your app's **Settings > Secrets** in the Streamlit Cloud UI (the
`secrets.toml` file itself is git-ignored and never pushed).

## 3. Verify the data and run the app

Install dependencies and start Streamlit:

```bash
pip install -r requirements.txt
streamlit run app.py
```

To diagnose Supabase access before starting Streamlit, run:

```bash
python db/check_supabase_access.py
```

The diagnostic reads `SUPABASE_URL` and `SUPABASE_KEY` from `.env`, tests all
ten dashboard tables in the `asset_management` schema, verifies the required
columns, and reports the accessible row count. To test one table only:

```bash
python db/check_supabase_access.py --table Clients
```

The script exits with status `0` when all requested checks pass and status `1`
when credentials are missing, the client cannot be created, or a table check
fails. It never prints the Supabase key.

Before loading dashboard data, the app checks every expected table for its
required columns. Empty core tables (`Investmentadvisors`, `Clients`,
`Accounts`, `Portfolios`, `Assets`, and `Portfolioholdings`) stop startup;
empty supporting tables produce warnings for the affected dashboard sections.
The app displays the specific table or column problem when validation fails.

The optional CSV utility can still refresh existing tables when needed. It
uses the `service_role` key and the configured `asset_management` schema:

```bash
python scripts/load_csv_to_supabase.py --data-dir ./data
```

The sidebar lets you widen the performance-history lookback window and
force-refresh cached Supabase data (cache TTL is 10 minutes by default —
see `CACHE_TTL_SECONDS` in `config.py`).

## Notes on scaling

- Large tables (`Transactions`, `Portfolioperformancemetrics`,
  `Advisorperformancemetrics`) are pulled with a server-side date filter
  (`months_back`) so the app stays responsive — widen this from each page's
  sidebar control as needed.
- All Supabase reads paginate past PostgREST's default 1,000-row cap
  automatically (`db/supabase_client.py::fetch_all`).
- For very large production datasets, consider replacing the client-side
  aggregations in `utils/metrics.py` with Postgres views or RPC functions
  (`supabase.rpc(...)`) so heavy grouping happens in the database rather
  than in pandas.

## Customizing

- Colors, table names, and cache TTL: `config.py`
- Add a new page: drop a new file in `pages/` following the
  `N_<emoji>_Title.py` naming convention — Streamlit picks it up automatically.
- Add a new KPI or chart: extend `utils/metrics.py` and/or `utils/charts.py`,
  then call it from the relevant page.
