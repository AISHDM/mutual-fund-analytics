"""
=============================================================
  Bluestock Fintech – Capstone Project I: Mutual Fund Analytics
  DAY 2 – Data Cleaning Pipeline
  Author  : Dheeraj (iamrealdheeraj16)
  Date    : 2026-06-24
=============================================================
  Cleans:
    • nav_history.csv
    • investor_transactions.csv
    • scheme_performance.csv
    • All remaining CSVs (generic pass)
  Output  : data/processed/<name>_clean.csv
=============================================================
"""

import warnings
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

warnings.filterwarnings("ignore")

# ── Paths ────────────────────────────────────────────────────
BASE_DIR      = Path(__file__).resolve().parent
RAW_DIR       = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
REPORTS_DIR   = BASE_DIR / "reports"
for d in [PROCESSED_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

SEP = "=" * 70


def section(t):
    print(f"\n{SEP}\n  {t}\n{SEP}")


def load(name: str) -> pd.DataFrame | None:
    path = RAW_DIR / name
    if not path.exists():
        # also check processed (in case Day 1 already saved there)
        path = PROCESSED_DIR / name.replace(".csv", "_clean.csv")
    if not path.exists():
        print(f"  ⚠️  {name} not found – skipping.")
        return None
    df = pd.read_csv(path, low_memory=False)
    print(f"  Loaded  {name}  →  {df.shape[0]:,} rows × {df.shape[1]} cols")
    return df


def save(df: pd.DataFrame, name: str):
    out = PROCESSED_DIR / name
    df.to_csv(out, index=False)
    print(f"  💾  Saved → {out.name}  ({len(df):,} rows)")


def find_col(df, candidates):
    """Return first matching column name."""
    for c in candidates:
        if c in df.columns:
            return c
    return None


# ════════════════════════════════════════════════════════════════
# 1.  NAV HISTORY
# ════════════════════════════════════════════════════════════════
def clean_nav_history() -> pd.DataFrame | None:
    section("1 · Cleaning nav_history.csv")
    df = load("nav_history.csv")
    if df is None:
        return None

    original_rows = len(df)
    log = []

    # ── Normalise column names ──────────────────────────────────
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    date_col  = find_col(df, ["date", "nav_date", "Date", "NAV_Date"])
    nav_col   = find_col(df, ["nav", "NAV", "net_asset_value", "nav_value"])
    code_col  = find_col(df, ["amfi_code", "scheme_code", "SchemeCode", "code"])

    # ── Parse dates → datetime ──────────────────────────────────
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], dayfirst=True, errors="coerce")
        bad_dates = df[date_col].isna().sum()
        if bad_dates:
            log.append(f"nav_history: {bad_dates} unparseable dates dropped")
        df.dropna(subset=[date_col], inplace=True)

    # ── Remove duplicates (amfi_code + date) ───────────────────
    subset = [c for c in [code_col, date_col] if c]
    before = len(df)
    df.drop_duplicates(subset=subset, keep="last", inplace=True)
    dups = before - len(df)
    if dups:
        log.append(f"nav_history: {dups} duplicate rows removed")
        print(f"  ♻️  Removed {dups} duplicate (amfi_code, date) rows")

    # ── Validate NAV > 0 ───────────────────────────────────────
    if nav_col:
        df[nav_col] = pd.to_numeric(df[nav_col], errors="coerce")
        invalid_nav = df[nav_col].isna() | (df[nav_col] <= 0)
        bad_nav_count = invalid_nav.sum()
        if bad_nav_count:
            log.append(f"nav_history: {bad_nav_count} rows with NAV ≤ 0 removed")
            print(f"  ❌  Dropped {bad_nav_count} rows with NAV ≤ 0 or NaN")
        df = df[~invalid_nav].copy()

    # ── Sort by amfi_code + date ────────────────────────────────
    sort_cols = [c for c in [code_col, date_col] if c]
    if sort_cols:
        df.sort_values(sort_cols, inplace=True)
        df.reset_index(drop=True, inplace=True)

    # ── Forward-fill missing NAV for weekends / holidays ───────
    if code_col and date_col and nav_col:
        # Create a full date range per fund and ffill
        groups = []
        for code, grp in df.groupby(code_col):
            full_idx = pd.date_range(grp[date_col].min(), grp[date_col].max(), freq="D")
            grp = grp.set_index(date_col).reindex(full_idx)
            grp.index.name = date_col
            grp[code_col] = code
            grp[nav_col] = grp[nav_col].ffill()
            grp = grp.dropna(subset=[nav_col])
            grp = grp.reset_index()
            groups.append(grp)
        if groups:
            df = pd.concat(groups, ignore_index=True)
            print(f"  📅  After forward-fill (weekends/holidays): {len(df):,} rows")
            log.append(f"nav_history: forward-filled NAV for holidays/weekends")

    print(f"  ✅  nav_history: {original_rows:,} → {len(df):,} rows after cleaning")
    save(df, "nav_history_clean.csv")
    _write_log("nav_history", log)
    return df


# ════════════════════════════════════════════════════════════════
# 2.  INVESTOR TRANSACTIONS
# ════════════════════════════════════════════════════════════════
def clean_investor_transactions() -> pd.DataFrame | None:
    section("2 · Cleaning investor_transactions.csv")
    df = load("investor_transactions.csv")
    if df is None:
        return None

    original_rows = len(df)
    log = []

    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    date_col   = find_col(df, ["date", "transaction_date", "txn_date"])
    type_col   = find_col(df, ["transaction_type", "txn_type", "type"])
    amount_col = find_col(df, ["amount", "txn_amount", "investment_amount"])
    kyc_col    = find_col(df, ["kyc_status", "kyc", "KYC_status"])

    # ── Fix date formats ────────────────────────────────────────
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], dayfirst=True, errors="coerce")
        bad = df[date_col].isna().sum()
        if bad:
            log.append(f"investor_transactions: {bad} bad dates dropped")
        df.dropna(subset=[date_col], inplace=True)

    # ── Standardise transaction_type ────────────────────────────
    VALID_TYPES = {"SIP", "Lumpsum", "Redemption"}
    TYPE_MAP = {
        # SIP variants
        "sip": "SIP", "s.i.p": "SIP", "systematic investment plan": "SIP",
        "systematic_investment": "SIP", "sip investment": "SIP",
        # Lumpsum variants
        "lumpsum": "Lumpsum", "lump sum": "Lumpsum", "lump_sum": "Lumpsum",
        "one time": "Lumpsum", "one_time": "Lumpsum", "onetime": "Lumpsum",
        "purchase": "Lumpsum",
        # Redemption variants
        "redemption": "Redemption", "redeem": "Redemption", "withdrawal": "Redemption",
        "sell": "Redemption", "switch_out": "Redemption",
    }
    if type_col:
        original_types = df[type_col].unique().tolist()
        df[type_col] = df[type_col].astype(str).str.strip().str.lower().map(
            lambda x: TYPE_MAP.get(x, x.title())
        )
        invalid_types = ~df[type_col].isin(VALID_TYPES)
        if invalid_types.sum():
            log.append(f"investor_transactions: {invalid_types.sum()} unknown transaction types flagged")
            print(f"  ⚠️  {invalid_types.sum()} rows with unknown transaction_type:")
            print(f"      {df.loc[invalid_types, type_col].value_counts().to_dict()}")
        print(f"  🔄  Standardised types: {original_types} → {sorted(VALID_TYPES)}")

    # ── Validate amount > 0 ─────────────────────────────────────
    if amount_col:
        df[amount_col] = pd.to_numeric(df[amount_col], errors="coerce")
        bad_amount = df[amount_col].isna() | (df[amount_col] <= 0)
        if bad_amount.sum():
            log.append(f"investor_transactions: {bad_amount.sum()} rows with amount ≤ 0 removed")
            print(f"  ❌  Removed {bad_amount.sum()} rows with amount ≤ 0")
        df = df[~bad_amount].copy()

    # ── Validate KYC status enum ────────────────────────────────
    VALID_KYC = {"KYC_VERIFIED", "KYC_PENDING", "KYC_REJECTED"}
    KYC_MAP   = {
        "verified": "KYC_VERIFIED", "kyc verified": "KYC_VERIFIED",
        "kyc_verified": "KYC_VERIFIED", "yes": "KYC_VERIFIED", "y": "KYC_VERIFIED",
        "pending": "KYC_PENDING",   "kyc pending": "KYC_PENDING",
        "kyc_pending": "KYC_PENDING", "no": "KYC_PENDING",
        "rejected": "KYC_REJECTED", "kyc rejected": "KYC_REJECTED",
        "kyc_rejected": "KYC_REJECTED",
    }
    if kyc_col:
        df[kyc_col] = df[kyc_col].astype(str).str.strip().str.lower().map(
            lambda x: KYC_MAP.get(x, x.upper())
        )
        invalid_kyc = ~df[kyc_col].isin(VALID_KYC)
        if invalid_kyc.sum():
            log.append(f"investor_transactions: {invalid_kyc.sum()} unknown KYC values")
            print(f"  ⚠️  {invalid_kyc.sum()} unknown KYC values: "
                  f"{df.loc[invalid_kyc, kyc_col].value_counts().to_dict()}")

    # ── Remove duplicates ───────────────────────────────────────
    before = len(df)
    df.drop_duplicates(inplace=True)
    dups = before - len(df)
    if dups:
        log.append(f"investor_transactions: {dups} duplicate rows removed")

    print(f"  ✅  investor_transactions: {original_rows:,} → {len(df):,} rows")
    save(df, "investor_transactions_clean.csv")
    _write_log("investor_transactions", log)
    return df


# ════════════════════════════════════════════════════════════════
# 3.  SCHEME PERFORMANCE
# ════════════════════════════════════════════════════════════════
def clean_scheme_performance() -> pd.DataFrame | None:
    section("3 · Cleaning scheme_performance.csv")
    df = load("scheme_performance.csv")
    if df is None:
        return None

    original_rows = len(df)
    log = []

    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    expense_col = find_col(df, ["expense_ratio", "expense ratio", "ter"])
    return_cols = [c for c in df.columns if any(k in c for k in
                   ["return", "cagr", "yield", "alpha", "beta", "sharpe", "std"])]

    # ── Validate all return values are numeric ──────────────────
    anomaly_rows = pd.Series(False, index=df.index)
    for col in return_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        nulls = df[col].isna().sum()
        if nulls:
            log.append(f"scheme_performance[{col}]: {nulls} non-numeric values → NaN")
            print(f"  ⚠️  {col}: {nulls} non-numeric → NaN")

        # Flag anomalies: returns outside [-50%, +200%] are suspicious
        if "return" in col or "cagr" in col:
            flag = df[col].notna() & ((df[col] < -50) | (df[col] > 200))
            anomaly_rows |= flag
            if flag.sum():
                log.append(f"scheme_performance[{col}]: {flag.sum()} anomalous return values")
                print(f"  🚩  {col}: {flag.sum()} anomalous values (< -50% or > 200%)")

    # ── Expense ratio range 0.1% – 2.5% ────────────────────────
    if expense_col:
        df[expense_col] = pd.to_numeric(df[expense_col], errors="coerce")
        # Handle if stored as decimal (0.01) vs percentage (1.0)
        if df[expense_col].dropna().median() < 0.1:
            df[expense_col] = df[expense_col] * 100   # convert to %
            print(f"  🔄  Converted {expense_col} from decimal to %")
        bad_exp = df[expense_col].notna() & ((df[expense_col] < 0.1) | (df[expense_col] > 2.5))
        if bad_exp.sum():
            log.append(f"scheme_performance: {bad_exp.sum()} expense_ratio values out of range (0.1%–2.5%)")
            print(f"  ⚠️  {bad_exp.sum()} expense_ratio values outside 0.1%–2.5% range → flagged")
            df.loc[bad_exp, "expense_ratio_flag"] = "OUT_OF_RANGE"

    # ── Save anomaly-flagged rows ───────────────────────────────
    if anomaly_rows.sum():
        anomaly_df = df[anomaly_rows].copy()
        anomaly_path = REPORTS_DIR / "scheme_performance_anomalies.csv"
        anomaly_df.to_csv(anomaly_path, index=False)
        print(f"  📋  {anomaly_rows.sum()} anomalous rows flagged → {anomaly_path.name}")

    df.drop_duplicates(inplace=True)
    df.reset_index(drop=True, inplace=True)

    print(f"  ✅  scheme_performance: {original_rows:,} → {len(df):,} rows")
    save(df, "scheme_performance_clean.csv")
    _write_log("scheme_performance", log)
    return df


# ════════════════════════════════════════════════════════════════
# 4.  GENERIC CLEANER for remaining CSVs
# ════════════════════════════════════════════════════════════════
def clean_remaining():
    section("4 · Generic Cleaning – Remaining CSVs")
    already_handled = {
        "nav_history.csv", "investor_transactions.csv", "scheme_performance.csv"
    }
    all_csvs = list(RAW_DIR.glob("*.csv")) + list(PROCESSED_DIR.glob("*_clean.csv"))
    raw_names = {f.name for f in RAW_DIR.glob("*.csv")}
    remaining = raw_names - already_handled

    if not remaining:
        print("  ℹ️  No additional CSVs to process.")
        return

    for fname in sorted(remaining):
        df = load(fname)
        if df is None:
            continue
        original = len(df)
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        df.drop_duplicates(inplace=True)
        # Coerce date-like columns
        for col in df.columns:
            if "date" in col or "time" in col:
                df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")
        out_name = fname.replace(".csv", "_clean.csv")
        save(df, out_name)
        print(f"  ✅  {fname}: {original:,} → {len(df):,} rows")


# ── Helper ──────────────────────────────────────────────────────
def _write_log(name: str, log: list[str]):
    if log:
        path = REPORTS_DIR / f"{name}_cleaning_log.txt"
        with open(path, "w") as f:
            f.write(f"Cleaning Log – {name} – {datetime.now()}\n{'='*50}\n")
            f.write("\n".join(log))
        print(f"  📝  Log → {path.name}")


# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print(f"\n{SEP}")
    print("  BLUESTOCK FINTECH – Day 2: Data Cleaning Pipeline")
    print(f"  Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(SEP)

    clean_nav_history()
    clean_investor_transactions()
    clean_scheme_performance()
    clean_remaining()

    section("✅  DATA CLEANING COMPLETE")
    cleaned = list(PROCESSED_DIR.glob("*_clean.csv"))
    print(f"  {len(cleaned)} clean files in data/processed/:")
    for f in sorted(cleaned):
        rows = sum(1 for _ in open(f)) - 1
        print(f"    • {f.name}  ({rows:,} rows)")
    print(f"\n  Next → run:  python db_loader.py\n")
