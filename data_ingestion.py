"""
=============================================================
  Bluestock Fintech – Capstone Project I: Mutual Fund Analytics
  DAY 1 – Data Ingestion (ETL)
  Author  : Dheeraj (iamrealdheeraj16)
  Date    : 2026-06-22
=============================================================
"""

import os
import sys
import warnings
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────
BASE_DIR       = Path(__file__).resolve().parent
RAW_DIR        = BASE_DIR / "data" / "raw"
PROCESSED_DIR  = BASE_DIR / "data" / "processed"
REPORTS_DIR    = BASE_DIR / "reports"

for d in [RAW_DIR, PROCESSED_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────
# EXPECTED DATASET NAMES (adjust if filenames differ)
# ─────────────────────────────────────────────
EXPECTED_FILES = [
    "fund_master.csv",
    "nav_history.csv",
    "amc_master.csv",
    "category_master.csv",
    "scheme_portfolio.csv",
    "fund_returns.csv",
    "risk_metrics.csv",
    "benchmark_data.csv",
    "expense_ratio.csv",
    "investor_transactions.csv",
]

SEPARATOR = "=" * 70


def section(title: str):
    print(f"\n{SEPARATOR}")
    print(f"  {title}")
    print(SEPARATOR)


# ─────────────────────────────────────────────
# 1. LOAD ALL CSV DATASETS
# ─────────────────────────────────────────────
def load_all_csvs() -> dict[str, pd.DataFrame]:
    """Load all CSVs from data/raw. Falls back to discovering all .csv files."""
    section("STEP 1 – Loading CSV Datasets from data/raw/")

    # Discover files: use expected list first, then auto-discover
    available = [f.name for f in RAW_DIR.glob("*.csv")]
    if not available:
        print("⚠️  No CSV files found in data/raw/")
        print(f"   Please place your 10 Bluestock CSV files in:  {RAW_DIR}")
        return {}

    # Match expected; if not found, use whatever is there
    files_to_load = [f for f in EXPECTED_FILES if f in available]
    extras        = [f for f in available if f not in EXPECTED_FILES]
    files_to_load.extend(extras)

    print(f"   Found {len(available)} CSV file(s) in raw directory.\n")

    datasets: dict[str, pd.DataFrame] = {}
    anomaly_log: list[str] = []

    for fname in files_to_load:
        fpath = RAW_DIR / fname
        key   = fname.replace(".csv", "")
        try:
            df = pd.read_csv(fpath, low_memory=False)
            datasets[key] = df

            print(f"📄  {fname}")
            print(f"    Shape   : {df.shape[0]:,} rows × {df.shape[1]} columns")
            print(f"    Columns : {list(df.columns)}")
            print(f"    dtypes  :\n{df.dtypes.to_string()}\n")
            print("    Head (3 rows):")
            print(df.head(3).to_string(index=False))
            print()

            # ── Anomaly Detection ────────────────────────────────────────
            nulls = df.isnull().sum()
            null_cols = nulls[nulls > 0]
            if not null_cols.empty:
                note = f"[{fname}] NULL values: {null_cols.to_dict()}"
                anomaly_log.append(note)
                print(f"    ⚠️  Nulls detected → {null_cols.to_dict()}")

            dups = df.duplicated().sum()
            if dups > 0:
                note = f"[{fname}] {dups} duplicate rows"
                anomaly_log.append(note)
                print(f"    ⚠️  {dups} duplicate rows found")

            print("-" * 60)

        except Exception as e:
            print(f"❌  Failed to load {fname}: {e}")

    # Save anomaly log
    if anomaly_log:
        log_path = REPORTS_DIR / "anomaly_log.txt"
        with open(log_path, "w") as f:
            f.write(f"Data Quality Anomaly Log – {datetime.now()}\n")
            f.write("=" * 60 + "\n")
            for note in anomaly_log:
                f.write(note + "\n")
        print(f"\n📝  Anomaly log saved → {log_path}")
    else:
        print("\n✅  No anomalies detected across all datasets.")

    return datasets


# ─────────────────────────────────────────────
# 2. EXPLORE FUND MASTER
# ─────────────────────────────────────────────
def explore_fund_master(datasets: dict[str, pd.DataFrame]):
    section("STEP 2 – Fund Master Exploration")

    key = "fund_master"
    if key not in datasets:
        print("⚠️  fund_master.csv not found. Skipping exploration.")
        return

    df = datasets[key]

    # Candidate column names (Bluestock may vary)
    col_map = {
        "fund_house"    : ["fund_house", "amc_name", "AMC", "amc", "FundHouse"],
        "category"      : ["category", "Category", "scheme_category"],
        "sub_category"  : ["sub_category", "subcategory", "Sub_Category", "scheme_sub_category"],
        "risk_grade"    : ["risk_grade", "risk", "Risk", "RiskGrade", "riskometer"],
        "scheme_code"   : ["scheme_code", "SchemeCode", "amfi_code", "scheme_id", "code"],
    }

    def find_col(df, candidates):
        for c in candidates:
            if c in df.columns:
                return c
        return None

    print(f"   Total schemes in fund_master: {len(df):,}\n")

    for field, candidates in col_map.items():
        col = find_col(df, candidates)
        if col:
            unique_vals = df[col].dropna().unique()
            print(f"  📌  Unique {field}s  ({len(unique_vals)}):")
            for v in sorted(unique_vals):
                print(f"        {v}")
            print()
        else:
            print(f"  ⚠️  Column for '{field}' not found. Tried: {candidates}")

    # AMFI scheme code structure note
    sc_col = find_col(df, col_map["scheme_code"])
    if sc_col:
        sample_codes = df[sc_col].dropna().head(5).tolist()
        print(f"  📎  Sample AMFI codes: {sample_codes}")
        code_lengths = df[sc_col].dropna().astype(str).str.len().value_counts()
        print(f"  📎  Code length distribution:\n{code_lengths.to_string()}")


# ─────────────────────────────────────────────
# 3. VALIDATE AMFI CODES
# ─────────────────────────────────────────────
def validate_amfi_codes(datasets: dict[str, pd.DataFrame]):
    section("STEP 3 – AMFI Code Validation (fund_master ↔ nav_history)")

    if "fund_master" not in datasets or "nav_history" not in datasets:
        print("⚠️  Both fund_master.csv and nav_history.csv are required.")
        return

    fm = datasets["fund_master"]
    nh = datasets["nav_history"]

    # Detect scheme code columns
    def find_code_col(df):
        for c in ["scheme_code", "SchemeCode", "amfi_code", "scheme_id", "code"]:
            if c in df.columns:
                return c
        return None

    fm_col = find_code_col(fm)
    nh_col = find_code_col(nh)

    if not fm_col or not nh_col:
        print(f"⚠️  Could not detect scheme code columns.\n"
              f"   fund_master columns: {list(fm.columns)}\n"
              f"   nav_history columns: {list(nh.columns)}")
        return

    fm_codes = set(fm[fm_col].dropna().astype(str))
    nh_codes = set(nh[nh_col].dropna().astype(str))

    missing_in_nav  = fm_codes - nh_codes
    extra_in_nav    = nh_codes - fm_codes
    matched         = fm_codes & nh_codes

    print(f"   fund_master  : {len(fm_codes):,} unique AMFI codes")
    print(f"   nav_history  : {len(nh_codes):,} unique AMFI codes")
    print(f"   ✅ Matched   : {len(matched):,} codes")
    print(f"   ❌ In fund_master but NOT nav_history : {len(missing_in_nav)}")
    print(f"   ⚠️  In nav_history but NOT fund_master : {len(extra_in_nav)}")

    if missing_in_nav:
        print(f"\n   Missing codes (first 10): {list(missing_in_nav)[:10]}")

    # ── Data Quality Summary ──────────────────────────────────────────
    summary_lines = [
        "=" * 60,
        "DATA QUALITY SUMMARY – Day 1 Ingestion",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 60,
        f"Datasets loaded         : {len(datasets)}",
        f"AMFI codes in master    : {len(fm_codes):,}",
        f"AMFI codes in nav hist  : {len(nh_codes):,}",
        f"Matched codes           : {len(matched):,}",
        f"Missing from nav_history: {len(missing_in_nav)}",
        f"Extra in nav_history    : {len(extra_in_nav)}",
        "",
        "STATUS: " + ("✅ CLEAN" if not missing_in_nav else "⚠️  ISSUES FOUND – review missing codes"),
    ]

    summary_path = REPORTS_DIR / "data_quality_summary.txt"
    with open(summary_path, "w") as f:
        f.write("\n".join(summary_lines))
    print(f"\n📝  Data quality summary saved → {summary_path}")
    print("\n".join(summary_lines))


# ─────────────────────────────────────────────
# 4. SAVE PROCESSED SNAPSHOTS
# ─────────────────────────────────────────────
def save_processed(datasets: dict[str, pd.DataFrame]):
    section("STEP 4 – Saving Processed Snapshots")
    for name, df in datasets.items():
        out = PROCESSED_DIR / f"{name}_clean.csv"
        df.drop_duplicates().to_csv(out, index=False)
        print(f"   ✅  Saved → {out.name}  ({len(df):,} rows)")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + SEPARATOR)
    print("  BLUESTOCK FINTECH – Day 1: Data Ingestion")
    print(f"  Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(SEPARATOR)

    datasets = load_all_csvs()

    if datasets:
        explore_fund_master(datasets)
        validate_amfi_codes(datasets)
        save_processed(datasets)
        section("✅  DAY 1 DATA INGESTION COMPLETE")
        print("   Deliverables ready:")
        print("   • data/processed/  – clean CSVs")
        print("   • reports/anomaly_log.txt")
        print("   • reports/data_quality_summary.txt")
        print("\n   Next: run  python live_nav_fetch.py\n")
    else:
        print("\n⚠️  Place your Bluestock CSV files in:  data/raw/")
        print("   Then re-run this script.\n")
