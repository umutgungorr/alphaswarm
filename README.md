# AlphaSwarm ⚡

> **Autonomous Multi-Agent Market Intelligence Hub & Consensus Graph.**  
> Inspired by institutional quantitative research swarms and event-driven multi-agent consensus graphs (`TradingAgentsGraph.propagate()`).

[![CI](https://img.shields.io/badge/CI-Passing-brightgreen?style=flat-square)](https://github.com/umutgungorr/alphaswarm)
[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg?style=flat-square)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-0-success.svg?style=flat-square)](#)

---

## 🧠 Architecture Overview

Single-prompt AI market analysis is plagued by hallucinations, over-optimism, and lack of mathematical grounding. 

**AlphaSwarm** solves this by orchestrating a **Multi-Agent Consensus Graph** with mandatory mathematical ground-truth injection:

```text
                  ┌────────────────────────────────────────┐
                  │ 📊 Mathematical Ground-Truth Engine    │
                  │ (RSI-14, 50/200 SMA, MACD, Bollinger)  │
                  └───────────────────┬────────────────────┘
                                      │ (Telemetry Injection)
                ┌─────────────────────┼─────────────────────┐
                ▼                     ▼                     ▼
    ┌──────────────────────┐┌──────────────────────┐┌──────────────────────┐
    │ 📐 Aria Vance        ││ 📰 Marcus Cole       ││ 🛡️ Vesper Sterling   │
    │    [QUANT-01]        ││    [MACRO-02]        ││    [DEVIL-03]        │
    │ Technical Momentum,  ││ Institutional Flows, ││ Downside Volatility, │
    │ Support/Resistance   ││ Catalysts & Sent.    ││ Invalidation Traps   │
    └───────────┬──────────┘└──────────┬───────────┘└──────────┬───────────┘
                │                      │                       │
                └──────────────────────┼───────────────────────┘
                                       │ (Cross-Agent Debate)
                                       ▼
                       ┌───────────────────────────────┐
                       │ ⚖️ Sovereign AI [CHIEF-00]     │
                       │    Consensus Arbitrator Node  │
                       │ • Direction: BULL/BEAR/NEUTRAL│
                       │ • Conviction Score: 0-100%    │
                       │ • Hard Invalidation Stop      │
                       └───────────────┬───────────────┘
                                       ▼
                       ┌───────────────────────────────┐
                       │ 📄 Executive Intelligence     │
                       │ (Live Stream + HTML Dossier)  │
                       └───────────────────────────────┘
```

---

## 🚀 Key Highlights

- **Zero External Dependencies**: Pure Python standard library math and telemetry. No fragile heavyweight frameworks required.
- **Mathematical Ground-Truth Injection**: Real indicators (RSI 14, 50/200 SMA golden/death crosses, MACD histograms, Bollinger Bands, ATR) are computed and injected before any agent speaks. Agents never hallucinate prices.
- **Dedicated Devil's Advocate (Risk Manager)**: An autonomous agent specifically programmed to seek out thesis invalidation, liquidity traps, and asymmetric downside risks.
- **Multi-Round Debate Graph**: Agents cross-examine counter-arguments over configurable debate rounds (`-r 1..3`).
- **Live Terminal Dialogue Stream**: Colored agent badges and callsigns stream real-time debate progress.
- **Executive Dossier Export**: Generate high-end dark-mode **HTML Dossiers** or clean **Markdown Intelligence Reports** with a single flag.

---

## 📦 Installation

```bash
# Using uv (recommended)
uv tool install alphaswarm

# Using pip
pip install alphaswarm
```

---

## 🛠️ CLI Usage & Quick Start

### 1. Execute Multi-Agent Analysis
```bash
# Analyze Bitcoin with live debate stream
alphaswarm analyze BTC

# Analyze Nvidia with 2 debate rounds and save executive HTML dossier
alphaswarm analyze NVDA -r 2 -f html -o nvda_dossier.html
```

Terminal Output Preview:
```text
⚡ Ingesting telemetry and launching consensus swarm for BTC...
  Last Price: $64,250.00 (+2.45%) | RSI-14: 61.2 | 50/200: BULLISH_STACK
── Multi-Agent Debate Commencing ──

  📐 [R1 // QUANT-01] Aria Vance • BULLISH (68%)
    "Constructive upward bias for BTC. Technical backdrop favors dip-buying toward upper Bollinger band ($67,120.00)."
    + Strong Bullish Trend Stack: Price ($64,250.00) > SMA-50 ($61,400.00) > SMA-200 ($58,200.00).
    + MACD Histogram positive (+14.2000), expanding upward.

  📰 [R1 // MACRO-02] Marcus Cole • BULLISH (72%)
    "Macro liquidity and crypto-native narratives are providing strong tailwinds for BTC."
    + Institutional net-inflow acceleration across digital asset ETPs; BTC liquidity depth expanding.
    + Options skew reflects strong call-side delta demand and short-squeeze positioning.

  🛡️ [R1 // DEVIL-03] Vesper Sterling • BULLISH (65%)
    "Bullish risk parameters are manageable with strict stop discipline on BTC."
    + Dual confirmation between Technicals and Sentiment reduces asymmetric downside.
    - ⚠️ ATR Volatility is $2,140.00; unexpected whipsaw moves can trigger tight retail stops.

═════════════════════════════════════════════════════════════════
  ⚡ ALPHASWARM CONSENSUS DOSSIER // BTC
═════════════════════════════════════════════════════════════════
  Market Price:       $64,250.00
  Consensus Stance:   BULLISH (72% Conviction)
  Key Invalidation:   $60,395.00
  Horizon:            SWING_1_TO_4_WEEKS
  Thesis:             Consensus Swarm settles on BULLISH for BTC ($64,250.00) with 72% weighted conviction.
═════════════════════════════════════════════════════════════════
```

### 2. Rapid Multi-Asset Watchlist Screening
```bash
alphaswarm scan BTC ETH SOL NVDA AAPL
```
Output:
```text
⚡ AlphaSwarm Screening Watchlist (5 tickers)...
────────────────────────────────────────────────────────────────────────
Ticker   Price        24h %      RSI      Consensus       Conviction
────────────────────────────────────────────────────────────────────────
BTC      $64,250.00   +2.45%     61.2     BULLISH         72%
ETH      $3,410.00    -1.12%     48.5     NEUTRAL         50%
SOL      $149.20      +5.80%     68.4     STRONG_BULL     86%
NVDA     $126.40      +1.85%     59.0     BULLISH         70%
AAPL     $224.10      -0.40%     51.3     NEUTRAL         50%
────────────────────────────────────────────────────────────────────────
```

---

## 📖 Subcommands & Flags

| Subcommand | Description | Key Options |
|---|---|---|
| `analyze <TICKER>` | Run multi-agent debate & consensus | `-r, --rounds` (1..3), `-f md\|html\|json`, `-o, --output`, `--offline` |
| `scan <TICKERS...>` | Screen multiple assets simultaneously | `--offline` |

---

## 🧪 Testing

```bash
uv run pytest
```

---

## 📜 License

MIT License. Crafted with precision by [Umut Güngör](https://github.com/umutgungorr).
