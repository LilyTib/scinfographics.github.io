import json, re
from playwright.sync_api import sync_playwright
URL = "https://publicdashboards.dl.usda.gov/t/MRP_PUB/views/NewWorldScrewwormPublicReporting_17805168329840/SummaryDashboard?:embed=y&:isGuestRedirectFromVizportal=y"
boot = None
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    def on_resp(r):
        global boot
        if "bootstrapSession" in r.url:
            try: boot = r.text()
            except Exception: pass
    pg.on("response", on_resp)
    pg.goto(URL, wait_until="load", timeout=120000); pg.wait_for_timeout(15000); b.close()

# response = "<len>;<json><len>;<json>"
parts, i = [], 0
while i < len(boot):
    m = re.match(r"(\d+);", boot[i:]); n = int(m.group(1)); s = i + len(m.group(0))
    parts.append(json.loads(boot[s:s+n])); i = s + n
def walk(o, path=()):
    if isinstance(o, dict):
        yield path, o
        for k, v in o.items(): yield from walk(v, path + (k,))
    elif isinstance(o, list):
        for i, v in enumerate(o): yield from walk(v, path + (i,))
print("top keys:", [list(p.keys()) for p in parts])
dd = {}
for path, d in walk(parts):
    if "dataSegments" in d:
        for seg in d["dataSegments"].values():
            for c in seg.get("dataColumns", []):
                dd.setdefault(c["dataType"], []).extend(c["dataValues"])
        print("data dictionary at", path[:8], {k: len(v) for k, v in dd.items()})
def val(dtype, idx):
    if idx >= 0: return dd.get(dtype, [])[idx] if idx < len(dd.get(dtype, [])) else ("?", dtype, idx)
    return dd["cstring"][-idx-1]
for path, d in walk(parts):
    if "paneColumnsData" in d:
        name = next((str(x) for x in reversed(path) if isinstance(x, str) and x not in ("presModelHolder","genVizDataPresModel","presModelMap","vizData","genPresModelMapPresModel")), str(path[-3:]))
        pcd = d["paneColumnsData"]
        print(f"\n=== {name}   (path tail {path[-4:]})")
        for vc in pcd["vizDataColumns"]:
            cap = vc.get("fieldCaption")
            if not cap: continue
            for pi, ci in zip(vc["paneIndices"], vc["columnIndices"]):
                pc = pcd["paneColumnsList"][pi]["vizPaneColumns"][ci]
                idxs = pc.get("aliasIndices") or pc.get("valueIndices") or []
                vals = [val(vc["dataType"], k) for k in idxs[:10]]
                print(f"   {cap!r} [{vc['dataType']}] -> {vals}{' ...' if len(idxs) > 10 else ''}")
