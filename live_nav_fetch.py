"""
=============================================================
  Bluestock Fintech – Capstone Project I: Mutual Fund Analytics
  DAY 1 – Live NAV Fetch from mfapi.in
  Author  : Dheeraj (iamrealdheeraj16)
  Date    : 2026-06-22
=============================================================
  API used : https://api.mfapi.in/mf/<scheme_code>
  Docs     : https://www.mfapi.in/
=============================================================
"""

import os
import time
import json
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime

# ─────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────
BASE_DIR  = Path(__file__).resolve().parent
RAW_DIR   = BASE_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL  = "https://api.mfapi.in/mf"
SEPARATOR = "=" * 70

# ─────────────────────────────────────────────
# SCHEME REGISTRY
# ─────────────────────────────────────────────
# Primary: HDFC Top 100 Direct (as specified in task)
PRIMARY_SCHEME = {
    "code": 125497,
    "name": "HDFC Top 100 Direct Plan – Growth",
}

# 5 Key Schemes (as specified in task)
KEY_SCHEMES = [
    {"code": 119551, "name": "SBI Bluechip Fund – Direct Growth",    "house": "SBI"},
    {"code": 120503, "name": "ICICI Pru Bluechip Fund – Direct",     "house": "ICICI"},
    {"code": 118632, "name": "Nippon India Large Cap Fund – Direct",  "house": "Nippon"},
    {"code": 119092, "name": "Axis Bluechip Fund – Direct Growth",   "house": "Axis"},
    {"code": 120841, "name": "Kotak Bluechip Fund – Direct Growth",  "house": "Kotak"},
]


def section(title: str):
    print(f"\n{SEPARATOR}")
    print(f"  {title}")
    print(SEPARATOR)


# ─────────────────────────────────────────────
# FETCH SINGLE SCHEME
# ─────────────────────────────────────────────
def fetch_scheme_nav(scheme_code: int, scheme_name: str, retries: int = 3) -> dict | None:
    """Fetch full NAV history for a scheme from mfapi.in."""
    url = f"{BASE_URL}/{scheme_code}"
    for attempt in range(1, retries + 1):
        try:
            print(f"   ↗  GET {url}  (attempt {attempt})")
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            print(f"   ✅  {scheme_name}")
            print(f"       Scheme  : {data.get('meta', {}).get('scheme_name', 'N/A')}")
            print(f"       Fund    : {data.get('meta', {}).get('fund_house', 'N/A')}")
            print(f"       Category: {data.get('meta', {}).get('scheme_category', 'N/A')}")
            print(f"       Records : {len(data.get('data', []))} NAV entries")
            if data.get("data"):
                latest = data["data"][0]
                print(f"       Latest  : ₹{latest.get('nav')}  on {latest.get('date')}")
            return data
        except requests.exceptions.RequestException as e:
            print(f"   ⚠️  Attempt {attempt} failed: {e}")
            if attempt < retries:
                time.sleep(2)
    print(f"   ❌  Could not fetch scheme {scheme_code} after {retries} attempts.")
    return None


# ─────────────────────────────────────────────
# PARSE & SAVE AS CSV
# ─────────────────────────────────────────────
def save_nav_csv(data: dict, filename: str) -> pd.DataFrame | None:
    """Parse JSON response and save NAV history as CSV."""
    if not data or not data.get("data"):
        print(f"   ⚠️  No NAV data to save for {filename}")
        return None

    meta    = data.get("meta", {})
    records = data["data"]

    df = pd.DataFrame(records)
    df.columns = [c.lower().strip() for c in df.columns]

    # Enrich with metadata
    df["scheme_code"]     = meta.get("scheme_code", "")
    df["scheme_name"]     = meta.get("scheme_name", "")
    df["fund_house"]      = meta.get("fund_house", "")
    df["scheme_type"]     = meta.get("scheme_type", "")
    df["scheme_category"] = meta.get("scheme_category", "")
    df["fetched_at"]      = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Parse date and sort ascending
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
        df.sort_values("date", inplace=True)
        df.reset_index(drop=True, inplace=True)

    if "nav" in df.columns:
        df["nav"] = pd.to_numeric(df["nav"], errors="coerce")

    out_path = RAW_DIR / filename
    df.to_csv(out_path, index=False)
    print(f"   💾  Saved → {out_path}  ({len(df):,} rows)")
    return df


# ─────────────────────────────────────────────
# STEP 1 – PRIMARY SCHEME (HDFC Top 100)
# ─────────────────────────────────────────────
def fetch_primary():
    section("STEP 1 – Fetch HDFC Top 100 Direct (scheme 125497)")
    data = fetch_scheme_nav(PRIMARY_SCHEME["code"], PRIMARY_SCHEME["name"])
    if data:
        df = save_nav_csv(data, "nav_hdfc_top100_direct.csv")

        # Also save raw JSON
        json_path = RAW_DIR / "nav_hdfc_top100_direct_raw.json"
        with open(json_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"   📄  Raw JSON saved → {json_path}")
        return df
    return None


# ─────────────────────────────────────────────
# STEP 2 – 5 KEY SCHEMES
# ─────────────────────────────────────────────
def fetch_key_schemes():
    section("STEP 2 – Fetch 5 Key Bluechip Schemes")
    all_dfs = []
    summary_rows = []

    for scheme in KEY_SCHEMES:
        print(f"\n  [{scheme['house']}] {scheme['name']}")
        data = fetch_scheme_nav(scheme["code"], scheme["name"])
        time.sleep(0.5)  # polite delay

        if data:
            fname = f"nav_{scheme['house'].lower()}_bluechip.csv"
            df    = save_nav_csv(data, fname)
            if df is not None:
                all_dfs.append(df)
                nav_vals = df["nav"].dropna()
                summary_rows.append({
                    "scheme_code"  : scheme["code"],
                    "scheme_name"  : scheme["name"],
                    "fund_house"   : scheme["house"],
                    "total_records": len(df),
                    "earliest_date": df["date"].min().strftime("%Y-%m-%d") if "date" in df.columns else "N/A",
                    "latest_date"  : df["date"].max().strftime("%Y-%m-%d") if "date" in df.columns else "N/A",
                    "latest_nav"   : round(nav_vals.iloc[-1], 4) if len(nav_vals) else None,
                    "all_time_high": round(nav_vals.max(), 4) if len(nav_vals) else None,
                    "all_time_low" : round(nav_vals.min(), 4) if len(nav_vals) else None,
                })

    # ── Combined NAV file ────────────────────────────────────────────
    if all_dfs:
        combined = pd.concat(all_dfs, ignore_index=True)
        combined_path = RAW_DIR / "nav_combined_5_schemes.csv"
        combined.to_csv(combined_path, index=False)
        print(f"\n   📦  Combined NAV file → {combined_path}  ({len(combined):,} rows total)")

    # ── Summary table ─────────────────────────────────────────────────
    if summary_rows:
        section("SUMMARY – 5 Key Schemes NAV Overview")
        summary_df = pd.DataFrame(summary_rows)
        print(summary_df.to_string(index=False))

        summary_path = RAW_DIR / "key_schemes_summary.csv"
        summary_df.to_csv(summary_path, index=False)
        print(f"\n   📋  Summary saved → {summary_path}")

    return all_dfs


# ─────────────────────────────────────────────
# STEP 3 – QUICK STATS COMPARISON
# ─────────────────────────────────────────────
def compare_schemes(dfs: list[pd.DataFrame]):
    if not dfs:
        return
    section("STEP 3 – Quick 1-Year Return Comparison")

    cutoff = pd.Timestamp.now() - pd.DateOffset(years=1)
    rows = []

    for df in dfs:
        if "date" not in df.columns or "nav" not in df.columns:
            continue
        df_filtered = df[df["date"] >= cutoff].copy()
        if len(df_filtered) < 2:
            continue
        nav_1y_ago = df_filtered.iloc[0]["nav"]
        nav_latest = df_filtered.iloc[-1]["nav"]
        ret_1y     = ((nav_latest - nav_1y_ago) / nav_1y_ago) * 100
        rows.append({
            "fund_house"      : df_filtered.iloc[-1].get("fund_house", "N/A"),
            "latest_nav (₹)"  : round(nav_latest, 4),
            "1Y return (%)"   : round(ret_1y, 2),
        })

    if rows:
        print(pd.DataFrame(rows).sort_values("1Y return (%)", ascending=False).to_string(index=False))


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + SEPARATOR)
    print("  BLUESTOCK FINTECH – Day 1: Live NAV Fetch")
    print(f"  Source  : https://api.mfapi.in/mf/")
    print(f"  Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(SEPARATOR)

    fetch_primary()
    key_dfs = fetch_key_schemes()
    compare_schemes(key_dfs)

    section("✅  LIVE NAV FETCH COMPLETE")
    print("   Files saved in data/raw/:")
    for f in sorted(Path(RAW_DIR).glob("nav_*.csv")):
        print(f"   • {f.name}")
    print()
