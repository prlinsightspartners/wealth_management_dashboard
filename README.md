# Wealth & Asset Management — Executive Dashboard

A multi-page Streamlit dashboard for a Canadian institutional wealth & asset
management firm, reading live from Supabase. Built on the 10 core tables:
`InvestmentAdvisors`, `Clients`, `Accounts`, `Portfolios`, `Assets`,
`PortfolioHoldings`, `Transactions`, `ClientInteractions`,
`PortfolioPerformanceMetrics`, and `AdvisorPerformanceMetrics`.

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
├── config.py                       # Table names, theme colors, shared settings
├── requirements.txt
├── .env.example                    # Copy to .env for local dev
├── .gitignore
├── README.md
├── db/
│   └── supabase_client.py          # Connection + paginated fetch helper
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
│   └── schema.sql                  # Run in Supabase SQL Editor first
├── scripts/
│   └── load_csv_to_supabase.py     # One-time CSV -> Supabase loader
└── .streamlit/
    ├── config.toml                 # Theme
    └── secrets.toml.example        # Copy to secrets.toml for Streamlit Cloud
```

## 1. Set up Supabase

1. Create a project at [supabase.com](https://supabase.com).
2. Open **SQL Editor** and run the contents of `sql/schema.sql`. This creates
   all 10 tables with correct types, foreign keys, indexes, and a permissive
   read-only Row Level Security policy (adjust the policy for your real auth
   model before production use).
3. Grab your credentials from **Project Settings > API**:
   - `Project URL` → `SUPABASE_URL`
   - `anon` `public` key → `SUPABASE_KEY` (used by the Streamlit app; read-only)
   - `service_role` key → only used locally by the loader script below, never
     shipped to the deployed app

## 2. Load the synthetic data

Put your generated CSVs (e.g. `InvestmentAdvisors.csv`, `Clients.csv`, …) in a
`data/` folder at the project root, then:

```bash
pip install -r requirements.txt
cp .env.example .env          # fill in SUPABASE_URL + the service_role key
python scripts/load_csv_to_supabase.py --data-dir ./data
```

The script loads tables in dependency order (parents before children) and
upserts in batches, so it's safe to re-run if you regenerate the data.

Alternatively, for smaller tables you can use Supabase's **Table Editor >
Insert > Import data from CSV** directly, provided you load parent tables
first (advisors → clients → accounts → portfolios → assets → holdings /
transactions / interactions → the two metrics tables).

## 3. Configure the app's credentials

For local development, edit `.env` (already created in step 2) with the
**anon** key:

```
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your-anon-public-api-key
```

For Streamlit Community Cloud, instead copy `.streamlit/secrets.toml.example`
to `.streamlit/secrets.toml` locally to test, then set the same two keys
under your app's **Settings > Secrets** in the Streamlit Cloud UI (the
`secrets.toml` file itself is git-ignored and never pushed).

## 4. Run the app

```bash
streamlit run app.py
```

The sidebar lets you widen the performance-history lookback window and
force-refresh cached Supabase data (cache TTL is 10 minutes by default —
see `CACHE_TTL_SECONDS` in `config.py`).

## Notes on scaling

- Large tables (`Transactions`, `PortfolioPerformanceMetrics`,
  `AdvisorPerformanceMetrics`) are pulled with a server-side date filter
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
