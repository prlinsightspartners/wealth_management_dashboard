
begin;

alter table if exists "InvestmentAdvisors" rename to "Investmentadvisors";
alter table if exists "PortfolioHoldings" rename to "Portfolioholdings";
alter table if exists "ClientInteractions" rename to "Clientinteractions";
alter table if exists "PortfolioPerformanceMetrics" rename to "Portfolioperformancemetrics";
alter table if exists "AdvisorPerformanceMetrics" rename to "Advisorperformancemetrics";
grant usage on schema asset_management to anon, authenticated;
grant select on all tables in schema asset_management to anon, authenticated;

commit;
