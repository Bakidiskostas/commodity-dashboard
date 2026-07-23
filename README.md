<img src="banner_preview.png" alt="Commodity & Indicators Dashboard" width="100%">

# Commodity & Financial Indicators Dashboard

Interactive dashboard for correlating metal prices with macroeconomic indicators — built for procurement controlling.

### ▶️ [**Open the live dashboard**](https://bakidiskostas.github.io/commodity-dashboard/)

---

## What it includes

**Commodities** (Yahoo Finance + FRED)
- Precious Metals: Gold, Silver, Platinum, Palladium
- Base Metals: Copper, Aluminum, Zinc, Nickel (LME), Tin/Solder (LME)
- Energy: Brent Oil, WTI Oil, Natural Gas

**Financial Indicators** (FRED / St. Louis Fed)
- FX: USD Index (Broad), EUR/USD
- Interest Rates: Fed Funds Rate, ECB Main Refinancing Rate
- Bonds: US 10Y Treasury
- GDP: US & EU growth
- Inflation: US & EU CPI (YoY)
- Equities: S&P 500, NASDAQ, Dow Jones, VIX

**Forecast mode**
- Official FOMC median projections (Fed Funds, PCE inflation, GDP) as hatched bars
- Statistical fan charts for commodities (50% / 90% bands from historical volatility)

---

## Features

| Control | What it does |
|---|---|
| **Sidebar** | Click any row to toggle a series on/off |
| **1Y / 2Y / 5Y / 10Y** | Filter the time period |
| **Normalized (base=100)** | Rebase all series to 100 → compare correlation regardless of units |
| **Forecast** | Show FOMC projections + statistical fan charts |
| **MACRO filter** | Show only Rates / GDP / Inflation / PMI in the bottom chart |
| **Legend** | Each series shows its % return over the displayed period |
| **Divider** | Drag to resize the top/bottom charts |

> **Note on forecasts:** the fan chart is a statistical range derived from historical
> volatility (a random-walk model) — it is **not** a price prediction. It shows the
> plausible spread of outcomes, which is what matters for budget planning.

---

## Data sources

| Source | Used for | Cost |
|---|---|---|
| [Yahoo Finance](https://finance.yahoo.com) via `yfinance` | Exchange-traded commodities | Free |
| [FRED API](https://fred.stlouisfed.org/docs/api/fred/) | Macro indicators, LME metals, FOMC projections | Free (API key required) |

---

## Setup

```bash
# 1. Clone the repo
git clone https://github.com/Bakidiskostas/commodity-dashboard.git
cd commodity-dashboard

# 2. Install Python libraries
pip install yfinance pandas requests

# 3. Add your FRED API key (free: https://fredaccount.stlouisfed.org/apikeys)
#    Either as an environment variable:
export FRED_API_KEY=your_key_here
#    ...or in a local file (gitignored):
echo "your_key_here" > scripts/fred_key.txt

# 4. Fetch data (creates data/commodities.json & data/indicators.json)
python scripts/fetch_data.py

# 5. Serve the dashboard
python -m http.server 8000
# then open http://localhost:8000
```

On Windows, `start.bat` does steps 2–5 in one go, and `update.bat` refreshes the data.

---

## Automatic updates

A GitHub Action (`.github/workflows/update-data.yml`) runs every Monday at 06:00 UTC,
fetches fresh data and commits the JSON files. The dashboard on GitHub Pages then
serves the updated data automatically — no manual steps.

The FRED API key is stored as a repository secret (`FRED_API_KEY`), never in the code.

To run it manually: **Actions** → **Update Commodity Data** → **Run workflow**.

> The script aborts without writing files if too many downloads fail, so a bad run
> can never overwrite good data.

---

## Adding new indicators

Open `scripts/fetch_data.py` and add a line to the `INDICATORS` list:

```python
{"fred_id": "UNRATE", "label": "US Unemployment", "unit": "%",
 "category": "Macro", "chart_type": "line", "default_on": False},
```

Find FRED series IDs at [fred.stlouisfed.org](https://fred.stlouisfed.org/).
No changes to `index.html` are needed — the sidebar builds itself from the data.

---

## Project structure

```
commodity-dashboard/
├── index.html                    ← the dashboard
├── README.md
├── assets/
│   └── banner.svg
├── scripts/
│   ├── fetch_data.py             ← data fetcher
│   └── fred_key.txt              ← your API key (gitignored)
├── data/
│   ├── commodities.json          ← generated
│   └── indicators.json           ← generated
└── .github/workflows/
    └── update-data.yml           ← weekly auto-update
```

---

## Tech stack

Python (pandas, yfinance, requests) · Plotly.js · GitHub Actions · GitHub Pages
