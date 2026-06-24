"""
=============================================================
  Bluestock Fintech – Capstone Project I: Mutual Fund Analytics
  DAY 2 – SQLite DB Loader
  Author  : Dheeraj (iamrealdheeraj16)
  Date    : 2026-06-24
=============================================================
  • Reads schema.sql → creates bluestock_mf.db
  • Loads cleaned CSVs from data/processed/ using SQLAlchemy
  • Verifies row counts match source CSVs
  • Runs all 10 analytical queries and prints results
=============================================================
"""

import warnings
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime, date

warnings.filterwarnings("ignore")

try:
    from sqlalchemy import create_engine, text
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False
    print("⚠️  SQLAlchemy not installed. Run: pip install sqlalchemy")

# ── Paths ─────────────────────────────────────────────────────
BASE_DIR      = Path(__file__).resolve().parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
DB_PATH       = BASE_DIR / "bluestock_mf.db"
SCHEMA_PATH   = BASE_DIR / "schema.sql"
QUERIES_PATH  = BASE_DIR / "queries.sql"
SEP = "=" * 70


def section(t):
    print(f"\n{SEP}\n  {t}\n{SEP}")


# ── CSV → table name mapping ──────────────────────────────────
TABLE_MAP = {
    "nav_history_clean.csv"            : "fact_nav",
    "investor_transactions_clean.csv"  : "fact_transactions",
    "scheme_performance_clean.csv"     : "fact_performance",
    "fund_master_clean.csv"            : "dim_fund",
    "amc_master_clean.csv"             : "dim_fund",       # supplement
    "category_master_clean.csv"        : "dim_fund",
    "fund_returns_clean.csv"           : "fact_performance",
    "risk_metrics_clean.csv"           : "fact_performance",
    "benchmark_data_clean.csv"         : "fact_performance",
    "expense_ratio_clean.csv"          : "fact_performance",
}

# ═════════════════════════════════════════════════════════════
# 1. CREATE DATABASE FROM SCHEMA.SQL
# ═════════════════════════════════════════════════════════════
def create_database():
    section("STEP 1 – Creating SQLite Database")

    if not SCHEMA_PATH.exists():
        print(f"  ❌  schema.sql not found at {SCHEMA_PATH}")
        return False

    conn = sqlite3.connect(DB_PATH)
    schema_sql = SCHEMA_PATH.read_text()
    try:
        conn.executescript(schema_sql)
        conn.commit()
        print(f"  ✅  Database created → {DB_PATH.name}")
        # List tables
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        print(f"  📋  Tables created: {[t[0] for t in tables]}")
    except Exception as e:
        print(f"  ❌  Schema error: {e}")
        conn.close()
        return False

    conn.close()
    return True


# ═════════════════════════════════════════════════════════════
# 2. BUILD dim_date (calendar dimension)
# ═════════════════════════════════════════════════════════════
def populate_dim_date(start="2015-01-01", end=None):
    section("STEP 2 – Populating dim_date (Calendar Dimension)")
    if end is None:
        end = datetime.now().strftime("%Y-%m-%d")

    dates = pd.date_range(start=start, end=end, freq="D")
    rows = []
    for d in dates:
        fy_start = d.year if d.month >= 4 else d.year - 1
        rows.append({
            "date_sk"       : int(d.strftime("%Y%m%d")),
            "full_date"     : d.strftime("%Y-%m-%d"),
            "day"           : d.day,
            "month"         : d.month,
            "month_name"    : d.strftime("%B"),
            "quarter"       : (d.month - 1) // 3 + 1,
            "year"          : d.year,
            "week_of_year"  : d.isocalendar()[1],
            "day_of_week"   : d.weekday(),
            "day_name"      : d.strftime("%A"),
            "is_weekend"    : 1 if d.weekday() >= 5 else 0,
            "is_month_end"  : 1 if d == d + pd.offsets.MonthEnd(0) else 0,
            "is_quarter_end": 1 if (d.month in [3, 6, 9, 12] and
                                    d == d + pd.offsets.MonthEnd(0)) else 0,
            "financial_year": f"FY{fy_start}-{str(fy_start + 1)[2:]}",
        })

    df = pd.DataFrame(rows)

    if HAS_SQLALCHEMY:
        engine = create_engine(f"sqlite:///{DB_PATH}")
        df.to_sql("dim_date", engine, if_exists="replace", index=False)
    else:
        conn = sqlite3.connect(DB_PATH)
        df.to_sql("dim_date", conn, if_exists="replace", index=False)
        conn.close()

    print(f"  ✅  dim_date populated: {len(df):,} rows ({start} → {end})")
    return df


# ═════════════════════════════════════════════════════════════
# 3. LOAD CLEANED CSVs → SQLITE
# ═════════════════════════════════════════════════════════════
def load_csvs_to_sqlite():
    section("STEP 3 – Loading Cleaned CSVs into SQLite")

    if not PROCESSED_DIR.exists():
        print(f"  ❌  data/processed/ not found. Run data_cleaning.py first.")
        return {}

    clean_csvs = list(PROCESSED_DIR.glob("*_clean.csv"))
    if not clean_csvs:
        print("  ❌  No *_clean.csv files found. Run data_cleaning.py first.")
        return {}

    if HAS_SQLALCHEMY:
        engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
    else:
        engine = None

    row_counts = {}

    for csv_path in sorted(clean_csvs):
        table_name = TABLE_MAP.get(csv_path.name)
        if table_name is None:
            # Use filename as table name (strip _clean.csv)
            table_name = csv_path.stem.replace("_clean", "").replace("-", "_")

        try:
            df = pd.read_csv(csv_path, low_memory=False)
            src_rows = len(df)

            # ── Normalise columns ─────────────────────────────
            df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

            # ── Load using SQLAlchemy ─────────────────────────
            if engine:
                df.to_sql(table_name, engine, if_exists="append",
                          index=False, chunksize=5000)
            else:
                conn = sqlite3.connect(DB_PATH)
                df.to_sql(table_name, conn, if_exists="append",
                          index=False, chunksize=5000)
                conn.close()

            # ── Verify row count ──────────────────────────────
            conn_v = sqlite3.connect(DB_PATH)
            db_rows = conn_v.execute(
                f"SELECT COUNT(*) FROM {table_name}"
            ).fetchone()[0]
            conn_v.close()

            match = "✅" if db_rows >= src_rows else "⚠️"
            print(f"  {match}  {csv_path.name:45s} → "
                  f"table={table_name:25s}  "
                  f"src={src_rows:,}  db={db_rows:,}")
            row_counts[csv_path.name] = {"source": src_rows, "db": db_rows}

        except Exception as e:
            print(f"  ❌  Failed to load {csv_path.name}: {e}")

    return row_counts


# ═════════════════════════════════════════════════════════════
# 4. ROW COUNT VERIFICATION REPORT
# ═════════════════════════════════════════════════════════════
def verify_row_counts(row_counts: dict):
    section("STEP 4 – Row Count Verification")
    all_match = True
    for fname, counts in row_counts.items():
        src, db = counts["source"], counts["db"]
        status = "✅ MATCH" if db >= src else "❌ MISMATCH"
        if db < src:
            all_match = False
        print(f"  {status}  {fname}: source={src:,}  db={db:,}")
    print(f"\n  {'✅  All row counts verified.' if all_match else '⚠️  Some mismatches – check above.'}")


# ═════════════════════════════════════════════════════════════
# 5. RUN 10 ANALYTICAL QUERIES
# ═════════════════════════════════════════════════════════════
QUERY_TITLES = [
    "Q1  · Top 5 Funds by AUM",
    "Q2  · Average NAV Per Month",
    "Q3  · SIP Year-over-Year Growth",
    "Q4  · Transactions by State (Top 10)",
    "Q5  · Funds with Expense Ratio < 1%",
    "Q6  · NAV 52-Week High and Low",
    "Q7  · Category-wise AUM Distribution",
    "Q8  · Top Performing Funds – 1Y Return",
    "Q9  · Monthly Transaction Volume by Type",
    "Q10 · KYC Compliance Rate by Fund House",
]


def run_queries():
    section("STEP 5 – Running 10 Analytical Queries")

    if not QUERIES_PATH.exists():
        print(f"  ❌  queries.sql not found.")
        return

    sql_text = QUERIES_PATH.read_text()

    import re
    # Split on the separator lines that precede each query block
    raw_blocks = re.split(r"\n--\s*─{20,}\n--\s*Q\d+", sql_text)
    queries = []
    for block in raw_blocks[1:]:
        lines = block.splitlines()
        # Skip first line (remainder of "Q5. Funds with..." header) and all -- comments
        clean_lines = [
            l for l in lines[1:]          # skip partial header line
            if not l.strip().startswith("--")
        ]
        clean_block = "\n".join(clean_lines)
        # Find from SELECT or WITH that starts a line
        m = re.search(r"^((?:WITH|SELECT)\b[\s\S]+)", clean_block, re.IGNORECASE | re.MULTILINE)
        if m:
            queries.append(m.group(1).strip())

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    results_store = {}

    for i, (title, sql) in enumerate(zip(QUERY_TITLES, queries)):
        print(f"\n  {'─'*60}")
        print(f"  {title}")
        print(f"  {'─'*60}")
        try:
            df = pd.read_sql_query(sql.strip(), conn)
            if df.empty:
                print("  ℹ️  No data returned (tables may be empty – add CSVs to data/raw/).")
            else:
                print(df.to_string(index=False, max_rows=10))
                results_store[title] = df
        except Exception as e:
            print(f"  ⚠️  Query error: {e}")

    conn.close()

    # Save results to reports/
    from pathlib import Path
    reports = BASE_DIR / "reports"
    reports.mkdir(exist_ok=True)
    for title, df in results_store.items():
        safe = title.replace(" ", "_").replace("·", "").replace("/", "-").strip("_")
        df.to_csv(reports / f"{safe}.csv", index=False)
    if results_store:
        print(f"\n  📊  Query results saved to reports/")


# ═════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print(f"\n{SEP}")
    print("  BLUESTOCK FINTECH – Day 2: SQLite DB Loader")
    print(f"  Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(SEP)

    ok = create_database()
    if not ok:
        print("\n❌  Database creation failed. Fix schema.sql and retry.")
        exit(1)

    populate_dim_date()
    row_counts = load_csvs_to_sqlite()

    if row_counts:
        verify_row_counts(row_counts)
    else:
        print("\n  ℹ️  No CSVs loaded yet — place cleaned files in data/processed/")
        print("      Then re-run this script.")

    run_queries()

    section("✅  DAY 2 DB LOADING COMPLETE")
    print(f"  Database : {DB_PATH}")
    print(f"  Git commit: git commit -m 'Day 2: Cleaned data + SQLite DB loaded'\n")
