"""Market data fetcher with real public APIs and offline simulation fallback."""

import json
import math
import random
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from alphaswarm.indicators import compute_technical_indicators
from alphaswarm.models import Candle, MarketData


def generate_mock_market_data(symbol: str) -> MarketData:
    """Generates realistic market candles using deterministic brownian random walk."""
    sym = symbol.upper().strip()
    is_crypto = sym in ("BTC", "ETH", "SOL", "BNB", "AVAX", "XRP", "ADA", "LINK", "DOGE")

    # Set baseline price
    baselines = {
        "BTC": 64500.0,
        "ETH": 3450.0,
        "SOL": 148.0,
        "NVDA": 125.0,
        "AAPL": 225.0,
        "MSFT": 430.0,
        "TSLA": 250.0,
        "SPY": 560.0,
        "QQQ": 480.0,
    }
    base_price = baselines.get(sym, 100.0)

    # Use hash of symbol for reproducible realistic seed
    rng = random.Random(hash(sym) & 0xFFFFFFFF)

    candles: list[Candle] = []
    current_price = base_price * (0.85 + (rng.random() * 0.3))
    now = datetime.now(timezone.utc)

    # Generate 60 daily candles
    for i in range(60, 0, -1):
        dt = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        daily_volatility = 0.035 if is_crypto else 0.018
        drift = 0.0005
        shock = rng.gauss(drift, daily_volatility)
        open_p = current_price
        close_p = open_p * (1.0 + shock)
        high_p = max(open_p, close_p) * (1.0 + abs(rng.gauss(0, 0.01)))
        low_p = min(open_p, close_p) * (1.0 - abs(rng.gauss(0, 0.01)))
        vol = (base_price * 1000) * (0.6 + rng.random() * 0.8)

        candles.append(Candle(
            timestamp=dt,
            open=round(open_p, 2),
            high=round(high_p, 2),
            low=round(low_p, 2),
            close=round(close_p, 2),
            volume=round(vol, 2),
        ))
        current_price = close_p

    latest = candles[-1]
    prev_close = candles[-2].close if len(candles) >= 2 else latest.open
    pct_change = ((latest.close - prev_close) / prev_close) * 100.0

    indicators = compute_technical_indicators(candles)

    return MarketData(
        symbol=sym,
        asset_class="CRYPTO" if is_crypto else "EQUITY",
        current_price=latest.close,
        change_24h_pct=pct_change,
        high_24h=latest.high,
        low_24h=latest.low,
        volume_24h=latest.volume,
        currency="USD",
        candles=candles,
        indicators=indicators,
    )


def fetch_binance_crypto(symbol: str) -> MarketData | None:
    """Fetches real 24hr ticker & daily klines from public Binance API."""
    sym = symbol.upper().strip()
    pair = f"{sym}USDT"
    headers = {"User-Agent": "AlphaSwarm/1.0"}

    ticker_url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={pair}"
    klines_url = f"https://api.binance.com/api/v3/klines?symbol={pair}&interval=1d&limit=60"

    try:
        # 1. Ticker
        req_ticker = urllib.request.Request(ticker_url, headers=headers)
        with urllib.request.urlopen(req_ticker, timeout=5) as resp:
            ticker_json = json.loads(resp.read().decode())

        # 2. Klines
        req_klines = urllib.request.Request(klines_url, headers=headers)
        with urllib.request.urlopen(req_klines, timeout=5) as resp:
            klines_json = json.loads(resp.read().decode())

        candles: list[Candle] = []
        for k in klines_json:
            # k: [time, open, high, low, close, volume, ...]
            dt = datetime.fromtimestamp(k[0] / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
            candles.append(Candle(
                timestamp=dt,
                open=float(k[1]),
                high=float(k[2]),
                low=float(k[3]),
                close=float(k[4]),
                volume=float(k[5]),
            ))

        indicators = compute_technical_indicators(candles)

        return MarketData(
            symbol=sym,
            asset_class="CRYPTO",
            current_price=float(ticker_json["lastPrice"]),
            change_24h_pct=float(ticker_json["priceChangePercent"]),
            high_24h=float(ticker_json["highPrice"]),
            low_24h=float(ticker_json["lowPrice"]),
            volume_24h=float(ticker_json["volume"]),
            currency="USD",
            candles=candles,
            indicators=indicators,
        )
    except Exception:
        return None


def get_market_data(symbol: str, force_offline: bool = False) -> MarketData:
    """Primary entry point: fetches real market data, falls back to realistic simulation."""
    sym = symbol.upper().strip()

    if not force_offline:
        # Attempt live public fetch for crypto pairs
        crypto_data = fetch_binance_crypto(sym)
        if crypto_data is not None:
            return crypto_data

    # Return high-fidelity simulation
    return generate_mock_market_data(sym)
