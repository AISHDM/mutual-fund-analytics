-- =============================================================
--  Bluestock Fintech – Capstone Project I: Mutual Fund Analytics
--  DAY 2 – 10 Analytical SQL Queries
--  Author : Dheeraj (iamrealdheeraj16)
--  Date   : 2026-06-24
--  DB     : bluestock_mf.db  (SQLite)
-- =============================================================

-- ─────────────────────────────────────────────────────────────
-- Q1. Top 5 Funds by AUM (latest month)
-- Business Question: Which funds have the highest assets under management?
-- ─────────────────────────────────────────────────────────────
SELECT
    f.fund_house,
    f.scheme_name,
    f.category,
    a.aum_crores,
    a.aum_date,
    RANK() OVER (ORDER BY a.aum_crores DESC) AS aum_rank
FROM fact_aum a
JOIN dim_fund f ON a.fund_sk = f.fund_sk
WHERE a.aum_date = (SELECT MAX(aum_date) FROM fact_aum)
ORDER BY a.aum_crores DESC
LIMIT 5;


-- ─────────────────────────────────────────────────────────────
-- Q2. Average NAV Per Month (per fund)
-- Business Question: How does NAV trend month-over-month?
-- ─────────────────────────────────────────────────────────────
SELECT
    f.scheme_name,
    f.fund_house,
    d.year,
    d.month,
    d.month_name,
    ROUND(AVG(n.nav), 4)  AS avg_nav,
    ROUND(MIN(n.nav), 4)  AS min_nav,
    ROUND(MAX(n.nav), 4)  AS max_nav,
    COUNT(*)              AS trading_days
FROM fact_nav n
JOIN dim_fund f ON n.fund_sk = f.fund_sk
JOIN dim_date d ON n.date_sk = d.date_sk
GROUP BY f.fund_sk, d.year, d.month
ORDER BY f.scheme_name, d.year, d.month;


-- ─────────────────────────────────────────────────────────────
-- Q3. SIP Year-over-Year Growth
-- Business Question: Is SIP adoption increasing annually?
-- ─────────────────────────────────────────────────────────────
WITH sip_yearly AS (
    SELECT
        d.year,
        COUNT(*)            AS sip_count,
        SUM(t.amount)       AS total_sip_amount,
        COUNT(DISTINCT t.investor_id) AS unique_investors
    FROM fact_transactions t
    JOIN dim_date d ON t.date_sk = d.date_sk
    WHERE t.transaction_type = 'SIP'
    GROUP BY d.year
)
SELECT
    year,
    sip_count,
    ROUND(total_sip_amount / 1e7, 2)   AS total_amount_crores,
    unique_investors,
    ROUND(
        100.0 * (sip_count - LAG(sip_count) OVER (ORDER BY year))
        / LAG(sip_count) OVER (ORDER BY year), 2
    ) AS yoy_growth_pct
FROM sip_yearly
ORDER BY year;


-- ─────────────────────────────────────────────────────────────
-- Q4. Transactions by State (Top 10)
-- Business Question: Which states drive the most investment volume?
-- ─────────────────────────────────────────────────────────────
SELECT
    state,
    COUNT(*)                            AS total_transactions,
    ROUND(SUM(amount) / 1e7, 2)        AS total_amount_crores,
    COUNT(DISTINCT investor_id)         AS unique_investors,
    ROUND(AVG(amount), 2)               AS avg_transaction_amount,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_of_total
FROM fact_transactions
WHERE state IS NOT NULL
GROUP BY state
ORDER BY total_amount_crores DESC
LIMIT 10;


-- ─────────────────────────────────────────────────────────────
-- Q5. Funds with Expense Ratio < 1%
-- Business Question: Which funds offer cost-efficient investing?
-- ─────────────────────────────────────────────────────────────
SELECT
    f.fund_house,
    f.scheme_name,
    f.category,
    f.sub_category,
    p.expense_ratio,
    p.return_1y,
    p.sharpe_ratio,
    ROUND(p.return_1y / p.expense_ratio, 2) AS return_per_cost_unit
FROM fact_performance p
JOIN dim_fund f ON p.fund_sk = f.fund_sk
WHERE p.expense_ratio < 1.0
  AND p.expense_ratio_flag IS NULL
  AND p.as_of_date = (SELECT MAX(as_of_date) FROM fact_performance)
ORDER BY p.expense_ratio ASC;


-- ─────────────────────────────────────────────────────────────
-- Q6. NAV 52-Week High and Low per Fund
-- Business Question: Which funds hit 52-week highs recently?
-- ─────────────────────────────────────────────────────────────
WITH nav_52w AS (
    SELECT
        n.amfi_code,
        MAX(n.nav)  AS high_52w,
        MIN(n.nav)  AS low_52w,
        MAX(n.nav_date) AS latest_date
    FROM fact_nav n
    WHERE n.nav_date >= DATE('now', '-365 days')
    GROUP BY n.amfi_code
),
latest_nav AS (
    SELECT amfi_code, nav AS current_nav
    FROM fact_nav
    WHERE nav_date = (SELECT MAX(nav_date) FROM fact_nav)
)
SELECT
    f.scheme_name,
    f.fund_house,
    l.current_nav,
    w.high_52w,
    w.low_52w,
    ROUND((l.current_nav - w.low_52w) / (w.high_52w - w.low_52w) * 100, 1) AS position_pct,
    CASE
        WHEN l.current_nav >= w.high_52w * 0.98 THEN '🔥 Near 52W High'
        WHEN l.current_nav <= w.low_52w  * 1.02 THEN '📉 Near 52W Low'
        ELSE '➡️ Mid Range'
    END AS position_label
FROM nav_52w w
JOIN latest_nav l  ON w.amfi_code = l.amfi_code
JOIN dim_fund  f   ON w.amfi_code = f.amfi_code
ORDER BY position_pct DESC;


-- ─────────────────────────────────────────────────────────────
-- Q7. Category-wise AUM Distribution
-- Business Question: How is investor money spread across fund categories?
-- ─────────────────────────────────────────────────────────────
SELECT
    f.category,
    COUNT(DISTINCT f.fund_sk)           AS num_funds,
    ROUND(SUM(a.aum_crores) / 1e3, 2)  AS total_aum_thousand_cr,
    ROUND(AVG(a.aum_crores), 2)         AS avg_aum_crores,
    ROUND(100.0 * SUM(a.aum_crores)
          / SUM(SUM(a.aum_crores)) OVER (), 2) AS market_share_pct
FROM fact_aum a
JOIN dim_fund f ON a.fund_sk = f.fund_sk
WHERE a.aum_date = (SELECT MAX(aum_date) FROM fact_aum)
GROUP BY f.category
ORDER BY total_aum_thousand_cr DESC;


-- ─────────────────────────────────────────────────────────────
-- Q8. Top Performing Funds – 1Y Return vs Expense Ratio
-- Business Question: Which funds give best risk-adjusted returns?
-- ─────────────────────────────────────────────────────────────
SELECT
    f.scheme_name,
    f.fund_house,
    f.category,
    ROUND(p.return_1y, 2)       AS return_1y_pct,
    ROUND(p.expense_ratio, 2)   AS expense_ratio_pct,
    ROUND(p.sharpe_ratio, 3)    AS sharpe_ratio,
    ROUND(p.alpha, 3)           AS alpha,
    RANK() OVER (PARTITION BY f.category ORDER BY p.return_1y DESC) AS rank_in_category
FROM fact_performance p
JOIN dim_fund f ON p.fund_sk = f.fund_sk
WHERE p.as_of_date = (SELECT MAX(as_of_date) FROM fact_performance)
  AND p.return_1y IS NOT NULL
ORDER BY f.category, rank_in_category
LIMIT 20;


-- ─────────────────────────────────────────────────────────────
-- Q9. Monthly Transaction Volume – SIP vs Lumpsum vs Redemption
-- Business Question: What is the monthly net flow trend?
-- ─────────────────────────────────────────────────────────────
SELECT
    d.year,
    d.month,
    d.month_name,
    ROUND(SUM(CASE WHEN t.transaction_type = 'SIP'        THEN t.amount ELSE 0 END) / 1e7, 2) AS sip_crores,
    ROUND(SUM(CASE WHEN t.transaction_type = 'Lumpsum'    THEN t.amount ELSE 0 END) / 1e7, 2) AS lumpsum_crores,
    ROUND(SUM(CASE WHEN t.transaction_type = 'Redemption' THEN t.amount ELSE 0 END) / 1e7, 2) AS redemption_crores,
    ROUND((
        SUM(CASE WHEN t.transaction_type IN ('SIP','Lumpsum') THEN t.amount ELSE 0 END)
        - SUM(CASE WHEN t.transaction_type = 'Redemption'     THEN t.amount ELSE 0 END)
    ) / 1e7, 2) AS net_flow_crores
FROM fact_transactions t
JOIN dim_date d ON t.date_sk = d.date_sk
GROUP BY d.year, d.month
ORDER BY d.year, d.month;


-- ─────────────────────────────────────────────────────────────
-- Q10. KYC Compliance Rate by Fund House
-- Business Question: Which AMCs have the highest KYC compliance?
-- ─────────────────────────────────────────────────────────────
SELECT
    f.fund_house,
    COUNT(*)                                                AS total_transactions,
    SUM(CASE WHEN t.kyc_status = 'KYC_VERIFIED'  THEN 1 ELSE 0 END) AS kyc_verified,
    SUM(CASE WHEN t.kyc_status = 'KYC_PENDING'   THEN 1 ELSE 0 END) AS kyc_pending,
    SUM(CASE WHEN t.kyc_status = 'KYC_REJECTED'  THEN 1 ELSE 0 END) AS kyc_rejected,
    ROUND(
        100.0 * SUM(CASE WHEN t.kyc_status = 'KYC_VERIFIED' THEN 1 ELSE 0 END)
        / COUNT(*), 2
    ) AS kyc_compliance_rate_pct
FROM fact_transactions t
JOIN dim_fund f ON t.fund_sk = f.fund_sk
GROUP BY f.fund_house
ORDER BY kyc_compliance_rate_pct DESC;
