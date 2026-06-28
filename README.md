# 📊 Commodity & Financial Indicators Dashboard

Interactive dashboard για συσχέτιση τιμών μετάλλων και οικονομικών δεικτών —
φτιαγμένο για Einkaufscontrolling.

## Τι περιλαμβάνει

**Commodities**
- Precious Metals: Gold, Silver, Platinum, Palladium
- Base Metals: Copper, Aluminum, Nickel, Zinc, Tin/Solder
- Energy: Brent Oil, WTI Oil, Natural Gas

**Financial Indicators** 
- USD Index (DXY), EUR/USD
- Intererst rates FED and ECB
- US & EU CPI (Inflation)
- S&P 500, VIX
- US 10Y Treasury Yield
- US & EU GDP Growth
- US PMI

## Χρήση

- **Sidebar**: κλικ σε κάθε γραμμή για ενεργοποίηση/απενεργοποίηση
- **1Ε / 2Ε / 5Ε / 10Ε**: φιλτράρισμα χρονικής περιόδου
- **Εξομαλυμένο (base=100)**: κανονικοποίηση όλων των σειρών στο 100
  → ιδανικό για να βλέπεις συσχέτιση ανεξάρτητα από μονάδες
- **Hover**: ενοποιημένο tooltip με όλες τις τιμές για μια ημερομηνία
- **Zoom**: σύρε στο chart για zoom, διπλό κλικ για reset


## GitHub Pages

1. Το dashboard τρέχει στο https://bakidiskostas.github.io/commodity-dashboard/


## GitHub Action αυτόματη ανανέωση

Δημιούργησε `.github/workflows/update-data.yml`:

```yaml
name: Update commodity data

on:
  schedule:
    - cron: '0 6 * * 1'   # κάθε Δευτέρα 06:00 UTC
  workflow_dispatch:        # manual trigger

jobs:
  fetch:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install yfinance pandas requests
      - run: python scripts/fetch_data.py
      - uses: actions/upload-artifact@v4
        with:
          name: data
          path: data/
      - uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: 'data: weekly update'
```

---

## Δομή αρχείων

```
commodity-dashboard/
├── index.html              ← Dashboard (άνοιξε στον browser)
├── README.md
├── scripts/
│   └── fetch_data.py       ← Python script για δεδομένα
└── data/
    ├── commodities.json    ← Δημιουργείται από το script
    └── indicators.json     ← Δημιουργείται από το script
```
