# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-09-24

### Added
- Mathematical ground-truth engine implementing zero-dependency Wilder's RSI, 50/200 SMA, MACD, Bollinger Bands, and ATR.
- Multi-Agent Consensus Graph architecture (`AlphaSwarmGraph.propagate()`) supporting multi-round debate.
- Four specialized autonomous market intelligence agents:
  - `TechnicalAnalystAgent` (Quant / Momentum / Support & Resistance)
  - `SentimentAnalystAgent` (Macro / Institutional Flows / Catalysts)
  - `RiskManagerAgent` (Devil's Advocate / Asymmetric Downside / Invalidation)
  - `ArbitratorAgent` (Consensus Synthesis / Conviction Scoring / Key Invalidation Stop)
- Market telemetry fetcher supporting live Binance crypto endpoint and deterministic offline simulation fallback.
- Rich terminal live stream with colored agent callsign badges.
- Executive dark-mode HTML Dossier generator with indicator cards and debate bubbles.
- Clean Markdown report generator.
- Multi-asset watchlist screening command (`scan`).
- Comprehensive automated pytest test suite.
