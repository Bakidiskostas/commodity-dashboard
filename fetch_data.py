"""
Commodity & Financial Indicators — Data Fetcher
"""
import json, os, requests, math, time
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf

YEARS_BACK = 10
END_DATE   = datetime.today()
START_DATE = END_DATE - timedelta(days=365 * YEARS_BACK)
DATA_DIR   = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)
FRED_BASE  = "https://api.stlouisfed.org/fred/series/observations"

def load_api_key():
    """API key from env var FRED_API_KEY, or from local file fred_key.txt (gitignored)."""
    key = os.environ.get("FRED_API_KEY", "").strip()
    if key:
        return key
    local = os.path.join(os.path.dirname(__file__), "fred_key.txt")
    if os.path.exists(local):
        with open(local, encoding="utf-8") as f:
            return f.read().strip()
    return ""

FRED_API_KEY = load_api_key()

# All commodities — including Nickel & Tin from FRED (LME)
# source: "yahoo" or "fred"
COMMODITIES = [
    # Precious Metals
    {"source":"yahoo","ticker":"GC=F",  "label":"Gold",              "unit":"USD/oz",    "category":"Precious Metals","chart_type":"line","default_on":True},
    {"source":"yahoo","ticker":"SI=F",  "label":"Silver",            "unit":"USD/oz",    "category":"Precious Metals","chart_type":"line","default_on":False},
    {"source":"yahoo","ticker":"PL=F",  "label":"Platinum",          "unit":"USD/oz",    "category":"Precious Metals","chart_type":"line","default_on":False},
    {"source":"yahoo","ticker":"PA=F",  "label":"Palladium",         "unit":"USD/oz",    "category":"Precious Metals","chart_type":"line","default_on":False},
    # Base Metals
    {"source":"yahoo","ticker":"HG=F",  "label":"Copper",            "unit":"USD/lb",    "category":"Base Metals",   "chart_type":"line","default_on":False},
    {"source":"fred", "ticker":"PALUMUSDM","label":"Aluminum (LME)",   "unit":"USD/MT",    "category":"Base Metals",   "chart_type":"line","default_on":False},
    {"source":"fred", "ticker":"PZINCUSDM","label":"Zinc (LME)",       "unit":"USD/MT",    "category":"Base Metals",   "chart_type":"line","default_on":False},
    {"source":"fred", "ticker":"PNICKUSDM","label":"Nickel (LME)",   "unit":"USD/MT",    "category":"Base Metals",   "chart_type":"line","default_on":False},
    {"source":"fred", "ticker":"PTINUSDM", "label":"Tin / Solder (LME)","unit":"USD/MT","category":"Base Metals",   "chart_type":"line","default_on":False},
    # Energy
    {"source":"yahoo","ticker":"BZ=F",  "label":"Brent Oil",         "unit":"USD/bbl",   "category":"Energy",        "chart_type":"line","default_on":False},
    {"source":"yahoo","ticker":"CL=F",  "label":"WTI Oil",           "unit":"USD/bbl",   "category":"Energy",        "chart_type":"line","default_on":False},
    {"source":"yahoo","ticker":"NG=F",  "label":"Natural Gas",       "unit":"USD/MMBtu", "category":"Energy",        "chart_type":"line","default_on":False},
]

INDICATORS = [
    # FX
    {"fred_id":"DTWEXBGS",           "label":"USD Index (Broad)",  "unit":"Index",  "category":"FX",            "chart_type":"line","default_on":False},
    {"fred_id":"DEXUSEU",            "label":"EUR/USD",            "unit":"Rate",   "category":"FX",            "chart_type":"line","default_on":False},
    # Interest Rates — BAR, default ON
    {"fred_id":"FEDFUNDS",           "label":"Fed Funds Rate",     "unit":"%",      "category":"Interest Rates","chart_type":"bar", "default_on":True},
    {"fred_id":"ECBMRRFR",             "label":"ECB Main Refinancing Rate",   "unit":"%",      "category":"Interest Rates","chart_type":"bar", "default_on":True},
    {"fred_id":"DGS10",              "label":"US 10Y Treasury",    "unit":"%",      "category":"Bonds",         "chart_type":"line","default_on":False},
    # GDP — BAR
    {"fred_id":"A191RL1Q225SBEA",    "label":"US GDP Growth",      "unit":"%",      "category":"GDP",           "chart_type":"bar", "default_on":False},
    {"fred_id":"CLVMNACSCAB1GQEA19","label":"EU GDP Growth","unit":"%",      "category":"GDP",           "chart_type":"bar", "default_on":False,"pct_change":True},
    # Inflation — BAR
    {"fred_id":"CPIAUCSL",           "label":"US Inflation (CPI YoY)","unit":"%",   "category":"Inflation",     "chart_type":"bar", "default_on":False,"pct_change_yoy":True},
    {"fred_id":"CP0000EZ19M086NEST", "label":"EU Inflation (CPI YoY)","unit":"%",   "category":"Inflation",     "chart_type":"bar", "default_on":False,"pct_change_yoy":True},
    # Industrial Activity
    {"fred_id":"INDPRO",             "label":"US Industrial Production","unit":"Index (2017=100)","category":"Industrial Activity","chart_type":"line","default_on":False},
    # Equities
    {"fred_id":"SP500",              "label":"S&P 500",            "unit":"Points", "category":"Equities",      "chart_type":"line","default_on":False},
    {"fred_id":"NASDAQCOM",          "label":"NASDAQ Composite",   "unit":"Points", "category":"Equities",      "chart_type":"line","default_on":False},
    {"fred_id":"DJIA",               "label":"Dow Jones (DJIA)",   "unit":"Points", "category":"Equities",      "chart_type":"line","default_on":False},
    {"fred_id":"VIXCLS",             "label":"VIX (Volatility)",   "unit":"Index",  "category":"Equities",      "chart_type":"line","default_on":False},
]

# Official FOMC projections (median, from FRED) — shown only in Forecast mode
PROJECTIONS = [
    {"fred_id":"FEDTARMD",  "label":"Fed Funds (FOMC Projection)",        "unit":"%","category":"Interest Rates","chart_type":"bar","default_on":False,"is_projection":True},
    {"fred_id":"PCECTPIMD", "label":"US Inflation PCE (FOMC Projection)", "unit":"%","category":"Inflation",     "chart_type":"bar","default_on":False,"is_projection":True},
    {"fred_id":"GDPC1MD",   "label":"US GDP (FOMC Projection)",           "unit":"%","category":"GDP",           "chart_type":"bar","default_on":False,"is_projection":True},
]

FORECAST_MONTHS = 12

# Futures chains on Yahoo for a market-implied forward path.
# ticker -> (root, exchange suffix, listed contract months)
FUTURES_CHAINS = {
    "GC=F": ("GC", ".CMX", [2, 4, 6, 8, 10, 12]),
    "SI=F": ("SI", ".CMX", [3, 5, 7, 9, 12]),
    "HG=F": ("HG", ".CMX", [3, 5, 7, 9, 12]),
    "PL=F": ("PL", ".NYM", [1, 4, 7, 10]),
    "PA=F": ("PA", ".NYM", [3, 6, 9, 12]),
    "CL=F": ("CL", ".NYM", list(range(1, 13))),
    "BZ=F": ("BZ", ".NYM", list(range(1, 13))),
    "NG=F": ("NG", ".NYM", list(range(1, 13))),
}
MONTH_CODE = {1:"F",2:"G",3:"H",4:"J",5:"K",6:"M",7:"N",8:"Q",9:"U",10:"V",11:"X",12:"Z"}

def fetch_futures_curve(ticker):
    """Return [(months_ahead, price), ...] from the listed futures chain.
    This is the market's own pricing of forward delivery — not a prediction.
    Returns None if the chain isn't available (e.g. LME metals)."""
    if ticker not in FUTURES_CHAINS:
        return None
    root, exch, months = FUTURES_CHAINS[ticker]
    today = END_DATE
    syms = {}
    for k in range(0, 16):                       # look ~15 months out
        y = today.year + (today.month - 1 + k) // 12
        m = (today.month - 1 + k) % 12 + 1
        if m not in months:
            continue
        sym = f"{root}{MONTH_CODE[m]}{str(y)[-2:]}{exch}"
        syms[sym] = k
    if len(syms) < 2:
        return None
    try:
        df = yf.download(list(syms.keys()), period="10d", interval="1d",
                         progress=False, auto_adjust=True, threads=True)
        if df is None or df.empty:
            return None
        close = df["Close"] if "Close" in df else None
        if close is None:
            return None
        pts = []
        for sym, k in syms.items():
            try:
                col = close[sym] if hasattr(close, "columns") and sym in close.columns else close
                v = col.dropna()
                if len(v):
                    pts.append((k, float(v.iloc[-1])))
            except Exception:
                continue
        pts = sorted(p for p in pts if p[1] > 0)
        return pts if len(pts) >= 2 else None
    except Exception as e:
        print(f"[curve {ticker}: {e}]", end=" ")
        return None

def curve_ratio(pts, m):
    """Forward price at month m relative to the nearest contract, linearly interpolated."""
    base = pts[0][1]
    if m <= pts[0][0]:
        return 1.0
    if m >= pts[-1][0]:
        return pts[-1][1] / base
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]; x1, y1 = pts[i + 1]
        if x0 <= m <= x1:
            w = 0 if x1 == x0 else (m - x0) / (x1 - x0)
            return (y0 + w * (y1 - y0)) / base
    return 1.0

def compute_fan(records, months=FORECAST_MONTHS, curve=None):
    """Fan chart: uncertainty bands from historical volatility, centred on the
    futures curve where one exists (otherwise flat — a random walk).
    The bands are a statistical range, NOT a price prediction."""
    n = len(records)
    if n < 40:
        return None
    dates = [datetime.strptime(r["date"], "%Y-%m-%d") for r in records]
    vals  = [r["value"] for r in records]
    span_days = (dates[-1] - dates[0]).days
    if span_days <= 0:
        return None
    step = span_days / (n - 1)                 # ~1 for daily, ~30 for monthly data
    per_month = max(1.0, 30.44 / step)         # observations per month
    lookback = int(min(n - 1, per_month * 24)) # ~2 years of history
    v = vals[-(lookback + 1):]
    rets = [math.log(v[i+1] / v[i]) for i in range(len(v) - 1) if v[i] > 0 and v[i+1] > 0]
    if len(rets) < 20:
        return None
    mu    = sum(rets) / len(rets)
    var   = sum((x - mu) ** 2 for x in rets) / (len(rets) - 1)
    sigma = math.sqrt(var)
    p0, d0 = vals[-1], dates[-1]
    out = {"dates": [], "median": [], "lo50": [], "hi50": [], "lo90": [], "hi90": [],
           "source": "futures" if curve else "flat"}
    for m in range(1, months + 1):
        s   = sigma * math.sqrt(per_month * m)
        mid = p0 * (curve_ratio(curve, m) if curve else 1.0)
        d   = d0 + timedelta(days=round(30.44 * m))
        out["dates"].append(d.strftime("%Y-%m-%d"))
        out["median"].append(round(mid, 4))
        out["lo50"].append(round(mid * math.exp(-0.674 * s), 4))
        out["hi50"].append(round(mid * math.exp( 0.674 * s), 4))
        out["lo90"].append(round(mid * math.exp(-1.645 * s), 4))
        out["hi90"].append(round(mid * math.exp( 1.645 * s), 4))
    return out

def series_to_records(series):
    series = series.dropna()
    return [{"date": d.strftime("%Y-%m-%d"), "value": round(float(v), 4)} for d, v in series.items()]

def fetch_yahoo(item):
    ticker = item["ticker"]
    print(f"  down {item['label']} ({ticker}) ...", end=" ")
    try:
        df = yf.download(ticker, start=START_DATE.strftime("%Y-%m-%d"),
                         end=END_DATE.strftime("%Y-%m-%d"), interval="1d",
                         auto_adjust=True, progress=False)
        if df.empty: print("WARNING empty"); return None
        records = series_to_records(df["Close"].squeeze())
        print(f"OK ({len(records)} records)")
        return {"id": ticker, **item, "data": records}
    except Exception as e:
        print(f"ERROR {e}"); return None

def fetch_fred(item):
    fid = item.get("fred_id") or item.get("ticker")
    print(f"  down {item['label']} ({fid}) ...", end=" ")
    try:
        last_err = None
        for attempt in range(4):
            try:
                r = requests.get(FRED_BASE, timeout=60, params={
                    "series_id": fid,
                    "api_key": FRED_API_KEY,
                    "file_type": "json",
                    "observation_start": START_DATE.strftime("%Y-%m-%d"),
                })
                r.raise_for_status()
                break
            except Exception as ex:
                last_err = ex
                print(f"retry {attempt+1}...", end=" ")
                time.sleep(4)
        else:
            raise last_err
        obs = r.json().get("observations", [])
        if not obs:
            print("WARNING empty"); return None
        df = pd.DataFrame(obs)[["date", "value"]]
        df["date"]  = pd.to_datetime(df["date"], errors="coerce")
        df["value"] = pd.to_numeric(df["value"], errors="coerce")   # "." -> NaN
        df = df.dropna(subset=["date"]).set_index("date")
        series = df["value"].sort_index()
        # Projections: keep only future years (current year overlaps the actual data)
        if item.get("is_projection"):
            series = series[series.index >= pd.Timestamp(END_DATE.year + 1, 1, 1)]
        # If pct_change=True, calculate quarter-over-quarter % change
        if item.get("pct_change"):
            series = series.pct_change() * 100
            series = series.dropna()
        # If pct_change_yoy=True, calculate year-over-year % change (12 periods for monthly)
        if item.get("pct_change_yoy"):
            series = series.pct_change(periods=12) * 100
            series = series.dropna()
        records = series_to_records(series)
        print(f"OK ({len(records)} records)")
        return {"id": fid, **item, "data": records}
    except Exception as e:
        print(f"ERROR {e}"); return None

def main():
    if not FRED_API_KEY:
        print("\nERROR: No FRED API key found.")
        print("  Local : create scripts/fred_key.txt containing your key")
        print("  Action: add repository secret FRED_API_KEY")
        raise SystemExit(1)
    print("=" * 60)
    print(f"  Commodity Dashboard — {START_DATE:%d/%m/%Y} -> {END_DATE:%d/%m/%Y}")
    print("=" * 60)
    print("\nCommodities")
    commodity_results = []
    for item in COMMODITIES:
        r = fetch_fred(item) if item["source"] == "fred" else fetch_yahoo(item)
        if r: commodity_results.append(r)

    # Fan charts — bands from volatility, median from the futures curve where available
    print("\nFutures curves (forward path)")
    for r in commodity_results:
        curve = fetch_futures_curve(r.get("ticker", "")) if r.get("source") == "yahoo" else None
        r["fan"] = compute_fan(r["data"], curve=curve)
        tag = "futures curve" if curve else "flat (no chain)"
        print(f"  {r['label']:<20} {tag}")

    print("\nFinancial Indicators (FRED)")
    indicator_results = []
    for item in INDICATORS + PROJECTIONS:
        r = fetch_fred(item)
        if r: indicator_results.append(r)
    if len(indicator_results) < 10 or len(commodity_results) < 8:
        print("\nERROR: Too many downloads failed - keeping old data.")
        raise SystemExit(1)


    meta = {"fetched_at": datetime.now().isoformat(),
            "start_date": START_DATE.strftime("%Y-%m-%d"),
            "end_date":   END_DATE.strftime("%Y-%m-%d")}
    out_c = os.path.join(DATA_DIR, "commodities.json")
    out_i = os.path.join(DATA_DIR, "indicators.json")
    with open(out_c, "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "series": commodity_results}, f, ensure_ascii=False, indent=2)
    with open(out_i, "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "series": indicator_results}, f, ensure_ascii=False, indent=2)
    print(f"\nSaved: {out_c}\n       {out_i}")
    print(f"\n   Commodities : {len(commodity_results)}/{len(COMMODITIES)}")
    print(f"   Indicators  : {len(indicator_results)}/{len(INDICATORS) + len(PROJECTIONS)}")

if __name__ == "__main__":
    main()