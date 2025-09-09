# Crypto Trading Strategy – Inter-IIT Submission

**Author:** Pushpendra Jain  
**Event:** Inter-IIT Tech Meet (Zelta Challenge)  
**Focus:** Designing, optimizing, and backtesting systematic trading strategies for BTC/ETH.

---

## 🔍 Overview

This repository contains the full research pipeline and final implementation of our crypto trading strategy.  
The work combines **regime detection**, **technical indicator optimization**, and a **backtesting framework** to deliver a robust systematic strategy.

Key highlights:
- **Volatility regime detection** (trend vs. range-bound markets).
- **Multi-indicator signal generation** using:
  - **Bollinger Bands**
  - **ATR & ADX/ADXR**
  - **Kaufman’s Adaptive Moving Average (KAMA)**
  - **True Strength Index (TSI)**
- **Dynamic strategy switching** between indicators depending on volatility.
- **Backtesting pipeline** for performance evaluation (Sharpe, drawdown, win-rate).
- Integration with **UnTrade backtesting client** for final evaluation.

---

## 📂 Repository Structure


```bash
Crypto_trading_Inter-IIT/
├── README.md
├── .gitignore
├── requirements.txt
│
├── data/                  # Raw datasets
│   ├── BTC_2019_2023_3d.csv
│   └── ETHUSDT_1d.csv
│
├── docs/                  # Reports & presentations
│   └── 84_h2_zelta_midterm.pdf
│
└── src/                   # Core code & notebooks
    ├── final_btc_strategy.py
    ├── backtesting_pipeline.ipynb
    ├── btc_indicator_optimisation.ipynb
    └── btc_regime_detection.ipynb

```

## ⚙️ Workflow

### 1. Regime Detection (`btc_regime_detection.ipynb`)
- Uses **ATR thresholds** to classify markets into:
  - **High volatility (trending)** → handled with KAMA, ADXR, TSI.
  - **Low volatility (range-bound)** → handled with Bollinger Bands.

### 2. Indicator Optimisation (`btc_indicator_optimisation.ipynb`)
- Runs parameter search for:
  - Bollinger Bands window size.
  - ATR & ADX thresholds.
  - KAMA fast/slow settings.
  - TSI smoothing lengths.
- Selects parameters that minimize drawdown while maximizing Sharpe ratio.

### 3. Backtesting Pipeline (`backtesting_pipeline.ipynb`)
- Loads optimized indicators.
- Applies trading rules (long/short entries, reversals, exits).
- Evaluates strategy metrics:
  - Sharpe ratio
  - Max drawdown
  - Win rate
  - Final portfolio value

### 4. Final Strategy (`final_btc_strategy.py`)
- Modularized pipeline with functions:
  - `process_data(data)` → add all indicators and signals.
  - `strat(data)` → apply regime-aware trading rules.
  - `perform_backtest(file)` → run UnTrade backtest.
- Saves results to `results.csv` and prints metrics.

---

## 🚀 Quickstart

### Installation
Clone repo & install dependencies:
```bash
git clone <repo-link>
cd Crypto_trading_Inter-IIT
pip install -r requirements.txt
python src/final_btc_strategy.py
