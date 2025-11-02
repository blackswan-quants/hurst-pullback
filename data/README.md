# Futures Datasets Summary

All datasets contain **daily OHLCV** complet data about trading days of various futures.

---

## ES – E-mini S&P 500
- **Source:** Yahoo Finance (`ES=F`)
- **Frequency:** Daily (1d)
- **Timezone:** UTC
- **File:** `ES.csv`
- **Columns:** Date, Open, High, Low, Close, Vol

---

## NQ – E-mini Nasdaq 100
- **Source:** Yahoo Finance (`NQ=F`)
- **Frequency:** Daily (1d)
- **Timezone:** UTC
- **File:** `NQ.csv`
- **Columns:** Date, Open, High, Low, Close, Vol

---

## YM – E-mini Dow Jones
- **Source:** Yahoo Finance (`YM=F`)
- **Frequency:** Daily (1d)
- **Timezone:** UTC
- **File:** `YM.csv`
- **Columns:** Date, Open, High, Low, Close, Vol

---

## EMD – E-mini S&P MidCap 400
- **Source:** Broker Data
- **Frequency:** Daily (1d)
- **Timezone:** UTC
- **File:** `EMD.csv`
- **Columns:** Date, Time, Open, High, Low, Close, Vol, OI

---

### Update Method
Data downloaded via `yfinance` library and some broker endpoint, aligned with market calendars (`pandas_market_calendars`), and missing days filled with forward fill (`ffill`).
