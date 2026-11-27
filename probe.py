import csv, io, urllib.request, collections, datetime as dt
URL = "https://publicdashboards.dl.usda.gov/t/MRP_PUB/views/NewWorldScrewwormPublicReporting_17805168329840/ExportToCSV.csv"
text = urllib.request.urlopen(urllib.request.Request(URL, headers={"User-Agent": "probe"}), timeout=60).read().decode("utf-8-sig")
rows = list(csv.DictReader(io.StringIO(text)))
print("columns:", list(rows[0].keys())); print("rows:", len(rows))
print("by Case Type:", collections.Counter(r["Case Type"] for r in rows))
print("by Domestic Status:", collections.Counter(r["Domestic Status"] for r in rows))
dom = [r for r in rows if r["Case Type"] == "Domestic"]
print("domestic by Status:", collections.Counter(r["Status"] for r in dom))
d = lambda r: dt.datetime.strptime(r["Confirmed Date"], "%m/%d/%Y")
print("domestic by month:", sorted(collections.Counter(d(r).strftime("%Y-%m") for r in dom).items()))
print("states:", collections.Counter(r["State"] for r in rows))
print("latest confirmed:", max(d(r) for r in rows).date(), " first:", min(d(r) for r in rows).date())
