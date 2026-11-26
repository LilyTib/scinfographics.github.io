#!/usr/bin/env python3
"""
Pull the latest confirmed New World screwworm case count from USDA APHIS's
public dashboard and save it to data/cases.json for the story page.

The dashboard is embedded on:
  https://www.aphis.usda.gov/animals/animal-health/livestock-and-poultry-disease/stop-screwworm/current-status/confirmed
Its summary view can be downloaded as CSV (monthly totals), which is what
this script reads. Standard library only, so it runs on any GitHub runner.

Usage:
  python3 scripts/update_cases.py            # download from USDA
  python3 scripts/update_cases.py --file x   # read a saved CSV (for testing)
"""
import csv
import datetime as dt
import io
import json
import pathlib
import sys
import urllib.request

CSV_URL = ("https://publicdashboards.dl.usda.gov/t/MRP_PUB/views/"
           "NewWorldScrewwormPublicReporting_17805168329840/SummaryDashboard.csv")
SOURCE_PAGE = ("https://www.aphis.usda.gov/animals/animal-health/livestock-and-poultry-disease/"
               "stop-screwworm/current-status/confirmed")
OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "cases.json"


def fetch_csv() -> str:
    req = urllib.request.Request(CSV_URL, headers={"User-Agent": "screwworm-story-updater/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8-sig")


def to_int(s: str):
    s = (s or "").replace(",", "").strip()
    return int(float(s)) if s else None


def parse(text: str) -> dict:
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows:
        raise ValueError("CSV is empty")
    cols = rows[0].keys()
    month_col = next((c for c in cols if "month" in c.lower()), None)
    total_col = next((c for c in cols if c.strip().lower() == "total cases"), None)
    dom_col = next((c for c in cols if c.strip().lower() == "total cases - domestic"), None)
    if not month_col or not total_col:
        raise ValueError(f"Expected columns not found; got {list(cols)}")

    months = []
    for r in rows:
        total = to_int(r.get(total_col))
        if total is None:
            continue
        label = r[month_col].strip()
        when = dt.datetime.strptime(label, "%B %Y")
        months.append({"month": label, "date": when, "total": total,
                       "domestic": to_int(r.get(dom_col)) if dom_col else None})
    if not months:
        raise ValueError("No monthly totals found")
    months.sort(key=lambda m: m["date"])
    latest = months[-1]
    out = {
        "total": sum(m["total"] for m in months),
        "domestic": sum(m["domestic"] or 0 for m in months) if dom_col else None,
        "latestMonth": latest["date"].strftime("%B"),
        "latestMonthYear": latest["month"],
        "latestMonthCases": latest["total"],
        "byMonth": [{"month": m["month"], "total": m["total"]} for m in months],
        "checked": dt.date.today().isoformat(),
        "source": SOURCE_PAGE,
    }
    if out["total"] <= 0:
        raise ValueError("Total is zero; refusing to overwrite")
    return out


def main() -> int:
    if len(sys.argv) == 3 and sys.argv[1] == "--file":
        text = pathlib.Path(sys.argv[2]).read_text(encoding="utf-8-sig")
    else:
        text = fetch_csv()
    data = parse(text)

    # Always rewrite, so the page's "as of" date shows the latest check.
    old = json.loads(OUT.read_text()) if OUT.exists() else {}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2) + "\n")
    print(f"Updated: {old.get('total')} -> {data['total']} cases (checked {data['checked']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
