# Data Dictionary – Bluestock Mutual Fund Analytics
**Capstone Project I · Bluestock Fintech 20J20**  
Author: Dheeraj (iamrealdheeraj16) · Date: 2026-06-24

---

## Overview

| Table | Type | Description |
|---|---|---|
| `dim_fund` | Dimension | Master list of all mutual fund schemes |
| `dim_date` | Dimension | Calendar dimension for time intelligence |
| `fact_nav` | Fact | Daily NAV per scheme |
| `fact_transactions` | Fact | Investor buy/SIP/redemption transactions |
| `fact_performance` | Fact | Periodic returns and risk metrics |
| `fact_aum` | Fact | Monthly AUM (Assets Under Management) per fund |

---

## dim_fund

**Source:** fund_master.csv, amc_master.csv  
**Grain:** One row per mutual fund scheme

| Column | Type | Nullable | Description | Example |
|---|---|---|---|---|
| `fund_sk` | INTEGER | No | Surrogate primary key (auto-increment) | 1 |
| `amfi_code` | TEXT | No | AMFI scheme code — unique identifier issued by AMFI India | 125497 |
| `scheme_name` | TEXT | No | Full official scheme name | HDFC Top 100 Direct Plan – Growth |
| `fund_house` | TEXT | No | AMC (Asset Management Company) name | HDFC Mutual Fund |
| `category` | TEXT | Yes | SEBI-defined broad category | Equity |
| `sub_category` | TEXT | Yes | SEBI sub-category | Large Cap |
| `scheme_type` | TEXT | Yes | Open-ended or Close-ended | Open-ended |
| `risk_grade` | TEXT | Yes | Risk level per SEBI Riskometer | Very High |
| `benchmark` | TEXT | Yes | Index used for performance comparison | NIFTY 100 TRI |
| `launch_date` | TEXT | Yes | Date of NFO launch (YYYY-MM-DD) | 2013-01-01 |
| `is_active` | INTEGER | No | 1 = active scheme, 0 = discontinued | 1 |
| `created_at` | TEXT | No | Record insertion timestamp | 2026-06-24 10:00:00 |

**Business Rules:**
- `amfi_code` must be unique; used as natural key across all fact tables
- `risk_grade` valid values: `Low`, `Moderately Low`, `Moderate`, `Moderately High`, `High`, `Very High`
- `category` valid values: `Equity`, `Debt`, `Hybrid`, `Solution Oriented`, `Other`

---

## dim_date

**Source:** Generated programmatically (2015-01-01 to present)  
**Grain:** One row per calendar day

| Column | Type | Nullable | Description | Example |
|---|---|---|---|---|
| `date_sk` | INTEGER | No | Surrogate key in YYYYMMDD format | 20240101 |
| `full_date` | TEXT | No | ISO date string (YYYY-MM-DD) | 2024-01-01 |
| `day` | INTEGER | No | Day of month (1–31) | 1 |
| `month` | INTEGER | No | Month number (1–12) | 1 |
| `month_name` | TEXT | No | Full month name | January |
| `quarter` | INTEGER | No | Calendar quarter (1–4) | 1 |
| `year` | INTEGER | No | Calendar year | 2024 |
| `week_of_year` | INTEGER | Yes | ISO week number (1–53) | 1 |
| `day_of_week` | INTEGER | Yes | 0=Monday … 6=Sunday | 0 |
| `day_name` | TEXT | Yes | Full day name | Monday |
| `is_weekend` | INTEGER | No | 1 if Saturday or Sunday, else 0 | 0 |
| `is_month_end` | INTEGER | No | 1 if last day of month, else 0 | 0 |
| `is_quarter_end` | INTEGER | No | 1 if last day of quarter, else 0 | 0 |
| `financial_year` | TEXT | Yes | Indian FY (April–March), e.g. FY2024-25 | FY2023-24 |

---

## fact_nav

**Source:** nav_history.csv (cleaned)  
**Grain:** One row per scheme per trading day

| Column | Type | Nullable | Description | Example |
|---|---|---|---|---|
| `nav_sk` | INTEGER | No | Surrogate primary key | 1 |
| `fund_sk` | INTEGER | No | FK → dim_fund.fund_sk | 1 |
| `date_sk` | INTEGER | No | FK → dim_date.date_sk | 20240101 |
| `amfi_code` | TEXT | No | AMFI scheme code (denormalised for query speed) | 125497 |
| `nav_date` | TEXT | No | Date of NAV declaration (YYYY-MM-DD) | 2024-01-01 |
| `nav` | REAL | No | Net Asset Value in ₹ — must be > 0 | 842.3421 |
| `nav_change` | REAL | Yes | Absolute NAV change from previous trading day | 3.25 |
| `nav_change_pct` | REAL | Yes | Percentage NAV change from previous trading day | 0.39 |
| `is_forward_filled` | INTEGER | No | 1 = NAV carried forward from previous day (holiday/weekend) | 0 |

**Business Rules:**
- `(amfi_code, nav_date)` must be unique
- `nav > 0` — enforced at DB level via CHECK constraint
- `is_forward_filled = 1` means no actual trading happened; NAV is same as last trading day
- Source of NAV: AMFI India daily NAV file / mfapi.in API

---

## fact_transactions

**Source:** investor_transactions.csv (cleaned)  
**Grain:** One row per investor transaction

| Column | Type | Nullable | Description | Example |
|---|---|---|---|---|
| `txn_sk` | INTEGER | No | Surrogate primary key | 1 |
| `fund_sk` | INTEGER | No | FK → dim_fund.fund_sk | 1 |
| `date_sk` | INTEGER | No | FK → dim_date.date_sk | 20240115 |
| `transaction_id` | TEXT | Yes | Unique transaction reference ID | TXN-20240115-00123 |
| `investor_id` | TEXT | No | Anonymised investor identifier | INV-00456 |
| `amfi_code` | TEXT | No | AMFI scheme code | 125497 |
| `transaction_date` | TEXT | No | Date of transaction (YYYY-MM-DD) | 2024-01-15 |
| `transaction_type` | TEXT | No | Type of transaction — `SIP`, `Lumpsum`, or `Redemption` | SIP |
| `amount` | REAL | No | Transaction amount in ₹ — must be > 0 | 5000.00 |
| `units` | REAL | Yes | Number of MF units bought/sold | 5.9382 |
| `nav_at_transaction` | REAL | Yes | NAV on transaction date | 841.85 |
| `state` | TEXT | Yes | Indian state of investor | Maharashtra |
| `kyc_status` | TEXT | Yes | KYC verification status | KYC_VERIFIED |
| `created_at` | TEXT | No | Record insertion timestamp | 2026-06-24 10:00:00 |

**Business Rules:**
- `transaction_type` valid values: `SIP`, `Lumpsum`, `Redemption` only
- `kyc_status` valid values: `KYC_VERIFIED`, `KYC_PENDING`, `KYC_REJECTED`
- `amount > 0` enforced via CHECK constraint
- SIP minimum: ₹500 | Lumpsum minimum: ₹1,000 (SEBI guidelines)

---

## fact_performance

**Source:** scheme_performance.csv, fund_returns.csv, risk_metrics.csv (cleaned)  
**Grain:** One row per scheme per reporting date

| Column | Type | Nullable | Description | Example |
|---|---|---|---|---|
| `perf_sk` | INTEGER | No | Surrogate primary key | 1 |
| `fund_sk` | INTEGER | No | FK → dim_fund.fund_sk | 1 |
| `date_sk` | INTEGER | No | FK → dim_date.date_sk | 20240331 |
| `amfi_code` | TEXT | No | AMFI scheme code | 125497 |
| `as_of_date` | TEXT | No | Performance snapshot date (YYYY-MM-DD) | 2024-03-31 |
| `return_1m` | REAL | Yes | 1-month absolute return % | 2.34 |
| `return_3m` | REAL | Yes | 3-month absolute return % | 7.12 |
| `return_6m` | REAL | Yes | 6-month absolute return % | 14.50 |
| `return_1y` | REAL | Yes | 1-year CAGR % | 28.75 |
| `return_3y` | REAL | Yes | 3-year CAGR % | 19.40 |
| `return_5y` | REAL | Yes | 5-year CAGR % | 16.20 |
| `expense_ratio` | REAL | Yes | Annual fund expense ratio in % | 0.82 |
| `sharpe_ratio` | REAL | Yes | Risk-adjusted return (higher = better) | 1.42 |
| `alpha` | REAL | Yes | Excess return over benchmark | 3.20 |
| `beta` | REAL | Yes | Volatility vs benchmark (1.0 = same) | 0.93 |
| `std_dev` | REAL | Yes | Standard deviation of returns (risk measure) | 12.40 |
| `expense_ratio_flag` | TEXT | Yes | `OUT_OF_RANGE` if expense_ratio < 0.1% or > 2.5% | NULL |

**Business Rules:**
- `(amfi_code, as_of_date)` must be unique
- `expense_ratio` valid range: 0.1% – 2.5% per SEBI regulations
- Returns flagged as anomalous if outside -50% to +200%
- `alpha > 0` means fund outperformed benchmark; `alpha < 0` means underperformed

---

## fact_aum

**Source:** aum_master.csv or derived from nav_history (cleaned)  
**Grain:** One row per scheme per month

| Column | Type | Nullable | Description | Example |
|---|---|---|---|---|
| `aum_sk` | INTEGER | No | Surrogate primary key | 1 |
| `fund_sk` | INTEGER | No | FK → dim_fund.fund_sk | 1 |
| `date_sk` | INTEGER | No | FK → dim_date.date_sk | 20240131 |
| `amfi_code` | TEXT | No | AMFI scheme code | 125497 |
| `aum_date` | TEXT | No | Month-end date for AUM snapshot (YYYY-MM-DD) | 2024-01-31 |
| `aum_crores` | REAL | No | AUM in ₹ Crores | 24381.45 |
| `aum_rank` | INTEGER | Yes | Fund rank by AUM among all schemes that month | 3 |

**Business Rules:**
- `(amfi_code, aum_date)` must be unique
- `aum_date` should always be a month-end date
- AUM reported in ₹ Crores (1 Crore = 10 million)
- Source: AMFI India monthly AUM disclosure

---

## Glossary

| Term | Definition |
|---|---|
| **AMFI** | Association of Mutual Funds in India — regulatory body that issues scheme codes |
| **AUM** | Assets Under Management — total market value of fund's investments |
| **NAV** | Net Asset Value — per-unit price of a mutual fund scheme |
| **CAGR** | Compound Annual Growth Rate — annualised return over a period |
| **Expense Ratio** | Annual fee charged by AMC as % of AUM (includes management + operating costs) |
| **Sharpe Ratio** | (Return − Risk-free rate) / Std Dev — measures return per unit of risk |
| **Alpha** | Fund return minus benchmark return — measures fund manager's skill |
| **Beta** | Sensitivity of fund returns to market movement (beta=1 means same as market) |
| **SIP** | Systematic Investment Plan — fixed periodic investment (monthly/weekly) |
| **KYC** | Know Your Customer — SEBI-mandated investor identity verification |
| **SEBI** | Securities and Exchange Board of India — regulates mutual funds and capital markets |
| **TRI** | Total Return Index — benchmark that includes dividends (more accurate than price index) |
| **FOF** | Fund of Funds — a mutual fund that invests in other mutual funds |
| **ELSS** | Equity Linked Savings Scheme — tax-saving mutual fund under Section 80C |
