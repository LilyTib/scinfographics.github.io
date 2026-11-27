#!/usr/bin/env python3
"""
Count confirmed New World screwworm cases in DOMESTIC animals from USDA
APHIS's public dashboard and save the result to data/cases.json.

Source: the dashboard's "Download Data" list (one row per detection):
  https://publicdashboards.dl.usda.gov/t/MRP_PUB/views/
      NewWorldScrewwormPublicReporting_17805168329840/ExportToCSV.csv
Each row has a "Case Type" of Domestic, Wildlife & Feral, or Fly Trap.
We count only "Domestic", which matches the dashboard's "Domestic Cases" box.

Usage:
  python3 scripts/update_cases.py            # download from USDA
  python3 scripts/update_cases.py --file x   # read a saved CSV (for testing)
"""
import collections
import csv
import datetime as dt
import io
import json
import pathlib
import sys
import urllib.request
from zoneinfo import ZoneInfo

CSV_URL = ("https://publicdashboards.dl.usda.gov/t/MRP_PUB/views/"
           "NewWorldScrewwormPublicReporting_17805168329840/ExportToCSV.csv")
SOURCE_PAGE = ("https://www.aphis.usda.gov/animals/animal-health/livestock-and-poultry-disease/"
               "stop-screwworm/current-status/confirmed")
OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "cases.json"
ET = ZoneInfo("America/New_York")


def fetch_csv() -> str:
    req = urllib.request.Request(CSV_URL, headers={"User-Agent": "screwworm-story-updater/2.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8-sig")


def data_date(now: dt.datetime) -> dt.date:
    """USDA refreshes the dashboard at 6pm ET, Monday-Saturday.
    Return the date of the most recent refresh."""
    d = now.date() if now.hour >= 18 else now.date() - dt.timedelta(days=1)
    while d.weekday() == 6:          # no Sunday update -> Saturday's data
        d -= dt.timedelta(days=1)
    return d


def parse(text: str, now: dt.datetime) -> dict:
    rows = list(csv.DictReader(io.StringIO(text)))
    need = {"Case Type", "Confirmed Date", "Status", "State"}
    if not rows or not need <= set(rows[0].keys()):
        raise ValueError(f"Unexpected CSV layout: {list(rows[0].keys()) if rows else 'empty'}")
    dom = [r for r in rows if r["Case Type"].strip() == "Domestic"]
    if not dom:
        raise ValueError("No domestic cases found; refusing to overwrite")
    when = lambda r: dt.datetime.strptime(r["Confirmed Date"].strip(), "%m/%d/%Y").date()
    latest = max(when(r) for r in dom)
    month_key = latest.strftime("%Y-%m")
    by_month = collections.Counter(when(r).strftime("%Y-%m") for r in dom)
    return {
        "total": len(dom),                                   # domestic animal cases, all time
        "active": sum(r["Status"].strip() == "Active" for r in dom),
        "states": len({r["State"].strip() for r in dom}),
        "latestMonth": latest.strftime("%B"),
        "latestMonthYear": latest.strftime("%B %Y"),
        "latestMonthCases": by_month[month_key],
        "latestDetection": latest.isoformat(),
        "byMonth": [{"month": dt.datetime.strptime(k, "%Y-%m").strftime("%B %Y"), "total": v}
                    for k, v in sorted(by_month.items())],
        "checked": data_date(now).isoformat(),              # date of USDA's latest refresh
        "countBasis": "Domestic animal cases (USDA Case Type = Domestic)",
        "source": SOURCE_PAGE,
    }


def main() -> int:
    now = dt.datetime.now(ET)
    if len(sys.argv) == 3 and sys.argv[1] == "--file":
        text = pathlib.Path(sys.argv[2]).read_text(encoding="utf-8-sig")
    else:
        text = fetch_csv()
    data = parse(text, now)
    old = json.loads(OUT.read_text()) if OUT.exists() else {}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2) + "\n")
    print(f"Domestic cases: {old.get('total')} -> {data['total']} "
          f"({data['active']} active; {data['latestMonthCases']} in {data['latestMonth']}); "
          f"data as of {data['checked']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
