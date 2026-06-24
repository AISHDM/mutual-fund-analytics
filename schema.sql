-- =============================================================
--  Bluestock Fintech – Capstone Project I: Mutual Fund Analytics
--  DAY 2 – SQLite Star Schema
--  Author : Dheeraj (iamrealdheeraj16)
--  Date   : 2026-06-24
-- =============================================================
--  Star Schema:
--    Dimensions : dim_fund, dim_date
--    Facts      : fact_nav, fact_transactions, fact_performance, fact_aum
-- =============================================================

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- ─────────────────────────────────────────────────────────────
-- DIMENSION: dim_fund
-- One row per mutual fund scheme
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_fund (
    fund_sk          INTEGER PRIMARY KEY AUTOINCREMENT,  -- surrogate key
    amfi_code        TEXT    NOT NULL UNIQUE,            -- AMFI scheme code (natural key)
    scheme_name      TEXT    NOT NULL,
    fund_house       TEXT    NOT NULL,                   -- AMC name (e.g. HDFC, SBI)
    category         TEXT,                               -- Equity / Debt / Hybrid
    sub_category     TEXT,                               -- Large Cap / Mid Cap etc.
    scheme_type      TEXT,                               -- Open-ended / Close-ended
    risk_grade       TEXT,                               -- Low / Moderate / High / Very High
    benchmark        TEXT,                               -- e.g. NIFTY 50 TRI
    launch_date      TEXT,                               -- ISO date string
    is_active        INTEGER DEFAULT 1,                  -- 1 = active, 0 = discontinued
    created_at       TEXT    DEFAULT (datetime('now'))
);

-- ─────────────────────────────────────────────────────────────
-- DIMENSION: dim_date
-- Calendar dimension for time intelligence
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_date (
    date_sk          INTEGER PRIMARY KEY,    -- YYYYMMDD integer key
    full_date        TEXT    NOT NULL UNIQUE, -- ISO: YYYY-MM-DD
    day              INTEGER NOT NULL,
    month            INTEGER NOT NULL,
    month_name       TEXT    NOT NULL,       -- January … December
    quarter          INTEGER NOT NULL,       -- 1–4
    year             INTEGER NOT NULL,
    week_of_year     INTEGER,
    day_of_week      INTEGER,                -- 0=Mon … 6=Sun
    day_name         TEXT,                  -- Monday … Sunday
    is_weekend       INTEGER DEFAULT 0,     -- 1 = Sat/Sun
    is_month_end     INTEGER DEFAULT 0,
    is_quarter_end   INTEGER DEFAULT 0,
    financial_year   TEXT                   -- e.g. FY2024-25
);

-- ─────────────────────────────────────────────────────────────
-- FACT: fact_nav
-- Daily NAV per fund
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_nav (
    nav_sk           INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_sk          INTEGER NOT NULL REFERENCES dim_fund(fund_sk),
    date_sk          INTEGER NOT NULL REFERENCES dim_date(date_sk),
    amfi_code        TEXT    NOT NULL,
    nav_date         TEXT    NOT NULL,
    nav              REAL    NOT NULL CHECK (nav > 0),
    nav_change       REAL,                  -- absolute change from prev day
    nav_change_pct   REAL,                  -- % change from prev day
    is_forward_filled INTEGER DEFAULT 0,   -- 1 = filled for holiday/weekend
    UNIQUE (amfi_code, nav_date)
);

-- ─────────────────────────────────────────────────────────────
-- FACT: fact_transactions
-- Investor buy/sell/SIP transactions
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_transactions (
    txn_sk              INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_sk             INTEGER NOT NULL REFERENCES dim_fund(fund_sk),
    date_sk             INTEGER NOT NULL REFERENCES dim_date(date_sk),
    transaction_id      TEXT    UNIQUE,
    investor_id         TEXT    NOT NULL,
    amfi_code           TEXT    NOT NULL,
    transaction_date    TEXT    NOT NULL,
    transaction_type    TEXT    NOT NULL CHECK (transaction_type IN ('SIP','Lumpsum','Redemption')),
    amount              REAL    NOT NULL CHECK (amount > 0),
    units               REAL,
    nav_at_transaction  REAL,
    state               TEXT,              -- Indian state of investor
    kyc_status          TEXT    CHECK (kyc_status IN ('KYC_VERIFIED','KYC_PENDING','KYC_REJECTED')),
    created_at          TEXT    DEFAULT (datetime('now'))
);

-- ─────────────────────────────────────────────────────────────
-- FACT: fact_performance
-- Periodic returns and risk metrics per scheme
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_performance (
    perf_sk          INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_sk          INTEGER NOT NULL REFERENCES dim_fund(fund_sk),
    date_sk          INTEGER NOT NULL REFERENCES dim_date(date_sk),
    amfi_code        TEXT    NOT NULL,
    as_of_date       TEXT    NOT NULL,
    return_1m        REAL,                  -- 1-month return %
    return_3m        REAL,
    return_6m        REAL,
    return_1y        REAL,
    return_3y        REAL,
    return_5y        REAL,
    expense_ratio    REAL,                  -- in %
    sharpe_ratio     REAL,
    alpha            REAL,
    beta             REAL,
    std_dev          REAL,
    expense_ratio_flag TEXT,               -- NULL or 'OUT_OF_RANGE'
    UNIQUE (amfi_code, as_of_date)
);

-- ─────────────────────────────────────────────────────────────
-- FACT: fact_aum
-- Assets Under Management per fund per month
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_aum (
    aum_sk           INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_sk          INTEGER NOT NULL REFERENCES dim_fund(fund_sk),
    date_sk          INTEGER NOT NULL REFERENCES dim_date(date_sk),
    amfi_code        TEXT    NOT NULL,
    aum_date         TEXT    NOT NULL,     -- typically month-end
    aum_crores       REAL    NOT NULL,     -- AUM in ₹ Crores
    aum_rank         INTEGER,              -- rank among all funds that month
    UNIQUE (amfi_code, aum_date)
);

-- ─────────────────────────────────────────────────────────────
-- INDEXES for query performance
-- ─────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_fact_nav_amfi_date     ON fact_nav(amfi_code, nav_date);
CREATE INDEX IF NOT EXISTS idx_fact_nav_date_sk       ON fact_nav(date_sk);
CREATE INDEX IF NOT EXISTS idx_fact_txn_amfi          ON fact_transactions(amfi_code);
CREATE INDEX IF NOT EXISTS idx_fact_txn_date          ON fact_transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_fact_txn_type          ON fact_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_fact_txn_state         ON fact_transactions(state);
CREATE INDEX IF NOT EXISTS idx_fact_perf_amfi         ON fact_performance(amfi_code);
CREATE INDEX IF NOT EXISTS idx_fact_aum_amfi          ON fact_aum(amfi_code, aum_date);
CREATE INDEX IF NOT EXISTS idx_dim_fund_house         ON dim_fund(fund_house);
CREATE INDEX IF NOT EXISTS idx_dim_fund_category      ON dim_fund(category);
