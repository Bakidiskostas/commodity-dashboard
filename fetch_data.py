"""
Commodity & Financial Indicators — Data Fetcher
"""
import json, os
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf

YEARS_BACK = 10
END_DATE   = datetime.today()
START_DATE = END_DATE - timedelta(days=365 * YEARS_BACK)
DATA_DIR   = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)
FRED_BASE  = "https://fred.stlouisfed.org/graph/fredgraph.csv"

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
    {"source":"yahoo","ticker":"ALI=F", "label":"Aluminum",          "unit":"USD/MT",    "category":"Base Metals",   "chart_type":"line","default_on":False},
    {"source":"yahoo","ticker":"ZC=F",  "label":"Zinc",              "unit":"USD/MT",    "category":"Base Metals",   "chart_type":"line","default_on":False},
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
    {"fred_id":"ECBMRROA",             "label":"ECB Main Refinancing Rate",   "unit":"%",      "category":"Interest Rates","chart_type":"bar", "default_on":True},
    {"fred_id":"DGS10",              "label":"US 10Y Treasury",    "unit":"%",      "category":"Bonds",         "chart_type":"line","default_on":False},
    # GDP — BAR
    {"fred_id":"A191RL1Q225SBEA",    "label":"US GDP Growth",      "unit":"%",      "category":"GDP",           "chart_type":"bar", "default_on":False},
    {"fred_id":"CLVMNACSCAB1GQEA19","label":"EU GDP Growth","unit":"%",      "category":"GDP",           "chart_type":"bar", "default_on":False,"pct_change":True},
    # Inflation — BAR
    {"fred_id":"CPIAUCSL",           "label":"US Inflation (CPI YoY)","unit":"%",   "category":"Inflation",     "chart_type":"bar", "default_on":False,"pct_change_yoy":True},
    {"fred_id":"CP0000EZ19M086NEST", "label":"EU Inflation (CPI YoY)","unit":"%",   "category":"Inflation",     "chart_type":"bar", "default_on":False,"pct_change_yoy":True},
    # PMI
    {"fred_id":"MANEMP",             "label":"US Manufacturing",   "unit":"Index",  "category":"PMI",           "chart_type":"line","default_on":False},
    # Equities
    {"fred_id":"SP500",              "label":"S&P 500",            "unit":"Points", "category":"Equities",      "chart_type":"line","default_on":False},
    {"fred_id":"NASDAQCOM",          "label":"NASDAQ Composite",   "unit":"Points", "category":"Equities",      "chart_type":"line","default_on":False},
    {"fred_id":"DJIA",               "label":"Dow Jones (DJIA)",   "unit":"Points", "category":"Equities",      "chart_type":"line","default_on":False},
    {"fred_id":"VIXCLS",             "label":"VIX (Volatility)",   "unit":"Index",  "category":"Equities",      "chart_type":"line","default_on":False},
]

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
        df = pd.read_csv(f"{FRED_BASE}?id={fid}", na_values=".")
        date_col, value_col = df.columns[0], df.columns[1]
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.dropna(subset=[date_col]).set_index(date_col)
        series = df[value_col].sort_index()
        series = series[series.index >= pd.Timestamp(START_DATE)]
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
    print("=" * 60)
    print(f"  Commodity Dashboard — {START_DATE:%d/%m/%Y} -> {END_DATE:%d/%m/%Y}")
    print("=" * 60)
    print("\nCommodities")
    commodity_results = []
    for item in COMMODITIES:
        r = fetch_fred(item) if item["source"] == "fred" else fetch_yahoo(item)
        if r: commodity_results.append(r)

    print("\nFinancial Indicators (FRED)")
    indicator_results = []
    for item in INDICATORS:
        r = fetch_fred(item)
        if r: indicator_results.append(r)

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
    print(f"   Indicators  : {len(indicator_results)}/{len(INDICATORS)}")

if __name__ == "__main__":
    main()
