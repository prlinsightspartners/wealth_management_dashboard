-- ============================================================================
-- Wealth & Asset Management — Supabase Schema
-- Run this in the Supabase SQL Editor (Project > SQL Editor > New Query)
-- BEFORE loading the CSV data (see scripts/load_csv_to_supabase.py or the
-- Supabase Table Editor's CSV import).
--
-- Tables are created in dependency order (parents before children) so that
-- foreign keys can be enforced.
-- ============================================================================

-- Drop in reverse-dependency order if you need to re-run this script cleanly.
-- Uncomment if you want a full reset:
-- drop table if exists "PortfolioPerformanceMetrics" cascade;
-- drop table if exists "AdvisorPerformanceMetrics" cascade;
-- drop table if exists "ClientInteractions" cascade;
-- drop table if exists "Transactions" cascade;
-- drop table if exists "PortfolioHoldings" cascade;
-- drop table if exists "Portfolios" cascade;
-- drop table if exists "Accounts" cascade;
-- drop table if exists "Clients" cascade;
-- drop table if exists "Assets" cascade;
-- drop table if exists "InvestmentAdvisors" cascade;

-- ----------------------------------------------------------------------------
-- 1. InvestmentAdvisors
-- ----------------------------------------------------------------------------
create table if not exists "InvestmentAdvisors" (
    "AdvisorID"     integer primary key,
    "FirstName"     text not null,
    "LastName"      text not null,
    "Email"         text,
    "PhoneNumber"   text,
    "HireDate"      date,
    "LicenseNumber" text,
    "Status"        text
);

-- ----------------------------------------------------------------------------
-- 2. Clients
-- ----------------------------------------------------------------------------
create table if not exists "Clients" (
    "ClientID"         integer primary key,
    "AdvisorID"        integer references "InvestmentAdvisors"("AdvisorID"),
    "FirstName"        text not null,
    "LastName"         text not null,
    "DateOfBirth"      date,
    "Address"          text,
    "City"             text,
    "State"            text,           -- Canadian province/territory code (ON, QC, BC, ...)
    "PostalCode"       text,
    "Country"          text default 'Canada',
    "Email"            text,
    "PhoneNumber"      text,
    "RegistrationDate" date,
    "RiskTolerance"    text
);

-- ----------------------------------------------------------------------------
-- 3. Accounts
-- ----------------------------------------------------------------------------
create table if not exists "Accounts" (
    "AccountID"   integer primary key,
    "ClientID"    integer references "Clients"("ClientID"),
    "AccountType" text,
    "OpeningDate" date,
    "Status"      text,
    "Balance"     numeric(18,2)
);

-- ----------------------------------------------------------------------------
-- 4. Portfolios
-- ----------------------------------------------------------------------------
create table if not exists "Portfolios" (
    "PortfolioID"         integer primary key,
    "AccountID"           integer references "Accounts"("AccountID"),
    "PortfolioName"       text,
    "CreationDate"        date,
    "LastRebalanceDate"   date,
    "InvestmentStrategy"  text
);

-- ----------------------------------------------------------------------------
-- 5. Assets
-- ----------------------------------------------------------------------------
create table if not exists "Assets" (
    "AssetID"      integer primary key,
    "AssetName"    text not null,
    "AssetType"    text,      -- Equity, ETF, Fixed Income, Commodity, Currency, Mutual Fund
    "TickerSymbol" text,
    "ISIN"         text
);

-- ----------------------------------------------------------------------------
-- 6. PortfolioHoldings
-- ----------------------------------------------------------------------------
create table if not exists "PortfolioHoldings" (
    "HoldingID"     integer primary key,
    "PortfolioID"   integer references "Portfolios"("PortfolioID"),
    "AssetID"       integer references "Assets"("AssetID"),
    "Quantity"      numeric(18,4),
    "PurchaseDate"  date,
    "PurchasePrice" numeric(18,4),
    "CurrentPrice"  numeric(18,4),
    "LastUpdated"   timestamp
);

-- ----------------------------------------------------------------------------
-- 7. Transactions
-- ----------------------------------------------------------------------------
create table if not exists "Transactions" (
    "TransactionID"   integer primary key,
    "AccountID"       integer references "Accounts"("AccountID"),
    "AssetID"         integer references "Assets"("AssetID"),
    "TransactionType" text,
    "TransactionDate" timestamp,
    "Quantity"        numeric(18,4),
    "PricePerUnit"    numeric(18,4),
    "Amount"          numeric(18,2),
    "Commission"      numeric(12,2)
);

-- ----------------------------------------------------------------------------
-- 8. ClientInteractions
-- ----------------------------------------------------------------------------
create table if not exists "ClientInteractions" (
    "InteractionID"   integer primary key,
    "ClientID"        integer references "Clients"("ClientID"),
    "AdvisorID"       integer references "InvestmentAdvisors"("AdvisorID"),
    "InteractionDate" timestamp,
    "InteractionType" text,
    "Notes"           text,
    "FollowUpDate"    date
);

-- ----------------------------------------------------------------------------
-- 9. PortfolioPerformanceMetrics
-- ----------------------------------------------------------------------------
create table if not exists "PortfolioPerformanceMetrics" (
    "MetricID"           integer primary key,
    "PortfolioID"        integer references "Portfolios"("PortfolioID"),
    "AUM"                numeric(18,2),
    "ReturnAbsolute"     numeric(10,5),
    "ReturnRiskAdjusted" numeric(10,4),
    "SharpeRatio"        numeric(10,3),
    "Alpha"              numeric(10,4),
    "Beta"               numeric(10,3),
    "CalculationDate"    date,
    "CreatedAt"          timestamp,
    "UpdatedAt"          timestamp
);

-- ----------------------------------------------------------------------------
-- 10. AdvisorPerformanceMetrics
-- ----------------------------------------------------------------------------
create table if not exists "AdvisorPerformanceMetrics" (
    "MetricID"            integer primary key,
    "AdvisorID"           integer references "InvestmentAdvisors"("AdvisorID"),
    "TotalAUM"            numeric(18,2),
    "AverageClientReturn" numeric(10,5),
    "NumberOfClients"     integer,
    "CalculationDate"     date,
    "CreatedAt"           timestamp,
    "UpdatedAt"           timestamp
);

-- ============================================================================
-- Indexes — speed up the filters and joins the dashboard performs most often
-- ============================================================================
create index if not exists idx_clients_advisor          on "Clients" ("AdvisorID");
create index if not exists idx_clients_state             on "Clients" ("State");
create index if not exists idx_accounts_client           on "Accounts" ("ClientID");
create index if not exists idx_portfolios_account        on "Portfolios" ("AccountID");
create index if not exists idx_holdings_portfolio        on "PortfolioHoldings" ("PortfolioID");
create index if not exists idx_holdings_asset            on "PortfolioHoldings" ("AssetID");
create index if not exists idx_transactions_account      on "Transactions" ("AccountID");
create index if not exists idx_transactions_asset        on "Transactions" ("AssetID");
create index if not exists idx_transactions_date         on "Transactions" ("TransactionDate");
create index if not exists idx_interactions_client       on "ClientInteractions" ("ClientID");
create index if not exists idx_interactions_advisor      on "ClientInteractions" ("AdvisorID");
create index if not exists idx_interactions_date         on "ClientInteractions" ("InteractionDate");
create index if not exists idx_pf_metrics_portfolio_date on "PortfolioPerformanceMetrics" ("PortfolioID", "CalculationDate");
create index if not exists idx_adv_metrics_advisor_date  on "AdvisorPerformanceMetrics" ("AdvisorID", "CalculationDate");

-- ============================================================================
-- Row Level Security — enable and allow read access for the dashboard's
-- anon/service role. Adjust policies to fit your actual auth model before
-- going to production; this default is permissive read-only access.
-- ============================================================================
alter table "InvestmentAdvisors" enable row level security;
alter table "Clients" enable row level security;
alter table "Accounts" enable row level security;
alter table "Portfolios" enable row level security;
alter table "Assets" enable row level security;
alter table "PortfolioHoldings" enable row level security;
alter table "Transactions" enable row level security;
alter table "ClientInteractions" enable row level security;
alter table "PortfolioPerformanceMetrics" enable row level security;
alter table "AdvisorPerformanceMetrics" enable row level security;

do $$
declare
    tbl text;
begin
    foreach tbl in array array[
        'InvestmentAdvisors','Clients','Accounts','Portfolios','Assets',
        'PortfolioHoldings','Transactions','ClientInteractions',
        'PortfolioPerformanceMetrics','AdvisorPerformanceMetrics'
    ]
    loop
        execute format('drop policy if exists "Allow read access on %I" on %I;', tbl, tbl);
        execute format(
            'create policy "Allow read access on %I" on %I for select using (true);',
            tbl, tbl
        );
    end loop;
end $$;
