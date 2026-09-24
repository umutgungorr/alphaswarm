"""Market data fetcher with real Binance & Yahoo Finance APIs and offline fallback."""

import json
import math
import random
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from alphaswarm.indicators import compute_technical_indicators
from alphaswarm.models import Candle, MarketData


# Verified Catalogs
COIN_CATALOGUE = {
    "BTC": {"name": "Bitcoin", "base_price": 64500.0, "vol": 0.035},
    "ETH": {"name": "Ethereum", "base_price": 3450.0, "vol": 0.040},
    "SOL": {"name": "Solana", "base_price": 148.0, "vol": 0.055},
    "BNB": {"name": "BNB", "base_price": 585.0, "vol": 0.030},
    "XRP": {"name": "XRP", "base_price": 0.58, "vol": 0.045},
    "ADA": {"name": "Cardano", "base_price": 0.38, "vol": 0.045},
    "DOGE": {"name": "Dogecoin", "base_price": 0.11, "vol": 0.060},
    "AVAX": {"name": "Avalanche", "base_price": 28.5, "vol": 0.050},
    "LINK": {"name": "Chainlink", "base_price": 11.8, "vol": 0.045},
    "SUI": {"name": "Sui", "base_price": 1.65, "vol": 0.065},
    "APT": {"name": "Aptos", "base_price": 8.20, "vol": 0.055},
    "NEAR": {"name": "NEAR Protocol", "base_price": 4.80, "vol": 0.050},
    "PEPE": {"name": "Pepe", "base_price": 0.0000085, "vol": 0.080},
    "DOT": {"name": "Polkadot", "base_price": 4.60, "vol": 0.045},
    "SHIB": {"name": "Shiba Inu", "base_price": 0.000014, "vol": 0.065},
    "LTC": {"name": "Litecoin", "base_price": 65.0, "vol": 0.035},
}

STOCK_CATALOGUE = {
    "NVDA": {"name": "NVIDIA Corp.", "base_price": 125.0, "vol": 0.025, "currency": "USD"},
    "AAPL": {"name": "Apple Inc.", "base_price": 225.0, "vol": 0.015, "currency": "USD"},
    "MSFT": {"name": "Microsoft Corp.", "base_price": 430.0, "vol": 0.016, "currency": "USD"},
    "TSLA": {"name": "Tesla Inc.", "base_price": 250.0, "vol": 0.035, "currency": "USD"},
    "AMZN": {"name": "Amazon.com Inc.", "base_price": 190.0, "vol": 0.020, "currency": "USD"},
    "GOOGL": {"name": "Alphabet Inc.", "base_price": 165.0, "vol": 0.018, "currency": "USD"},
    "META": {"name": "Meta Platforms Inc.", "base_price": 570.0, "vol": 0.022, "currency": "USD"},
    "AMD": {"name": "Advanced Micro Devices", "base_price": 155.0, "vol": 0.028, "currency": "USD"},
    "SPY": {"name": "SPDR S&P 500 ETF", "base_price": 560.0, "vol": 0.010, "currency": "USD"},
    "QQQ": {"name": "Invesco QQQ Trust", "base_price": 480.0, "vol": 0.014, "currency": "USD"},
    "PLTR": {"name": "Palantir Technologies", "base_price": 37.0, "vol": 0.035, "currency": "USD"},
    "COIN": {"name": "Coinbase Global Inc.", "base_price": 185.0, "vol": 0.045, "currency": "USD"},
    "NFLX": {"name": "Netflix Inc.", "base_price": 700.0, "vol": 0.020, "currency": "USD"},
    "THYAO": {"name": "Türk Hava Yolları", "base_price": 310.0, "vol": 0.022, "currency": "TRY"},
    "ASELS": {"name": "Aselsan", "base_price": 62.5, "vol": 0.020, "currency": "TRY"},
    "EREGL": {"name": "Ereğli Demir Çelik", "base_price": 52.0, "vol": 0.018, "currency": "TRY"},
    "GARAN": {"name": "Garanti BBVA", "base_price": 120.0, "vol": 0.024, "currency": "TRY"},
    "KCHOL": {"name": "Koç Holding", "base_price": 215.0, "vol": 0.020, "currency": "TRY"},
}


def calculate_fear_and_greed(rsi: float, change_24h: float, trend: str, vol_ratio: float) -> tuple[int, str]:
    """Computes a synthesized 0-100 Fear & Greed index score and descriptive label."""
    score = 50.0

    # RSI contribution (weight 40%)
    score += (rsi - 50.0) * 0.7

    # 24h momentum contribution (weight 25%)
    score += max(-20.0, min(20.0, change_24h * 2.5))

    # Trend contribution (weight 20%)
    if trend in ("BULLISH_STACK", "GOLDEN_CROSS"):
        score += 10.0
    elif trend in ("BEARISH_STACK", "DEATH_CROSS"):
        score -= 10.0

    # Volume expansion during uptrend/downtrend (weight 15%)
    if vol_ratio > 1.2 and change_24h > 0:
        score += 8.0
    elif vol_ratio > 1.2 and change_24h < 0:
        score -= 8.0

    final_score = int(max(5, min(95, round(score))))

    if final_score >= 75:
        label = "AŞIRI AÇGÖZLÜLÜK (EXTREME GREED)"
    elif final_score >= 58:
        label = "AÇGÖZLÜLÜK (GREED)"
    elif final_score <= 25:
        label = "AŞIRI KORKU (EXTREME FEAR)"
    elif final_score <= 42:
        label = "KORKU (FEAR)"
    else:
        label = "NÖTR / DENGELİ (NEUTRAL)"

    return final_score, label


def validate_symbol(symbol: str, asset_type: str | None = None) -> tuple[str, str]:
    sym = symbol.upper().strip()
    if not sym:
        raise ValueError("Lütfen geçerli bir sembol girin (Örn: BTC, NVDA).")

    if asset_type == "CRYPTO":
        if sym in COIN_CATALOGUE:
            return sym, "CRYPTO"
    elif asset_type == "EQUITY":
        if sym in STOCK_CATALOGUE:
            return sym, "EQUITY"

    if sym in COIN_CATALOGUE:
        return sym, "CRYPTO"
    if sym in STOCK_CATALOGUE:
        return sym, "EQUITY"

    # Quick online checks
    if asset_type in (None, "CRYPTO"):
        try:
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={sym}USDT"
            req = urllib.request.Request(url, headers={"User-Agent": "AlphaSwarm/1.0"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    return sym, "CRYPTO"
        except Exception:
            pass

    raise ValueError(
        f"'{sym}' geçerli bir Kripto Para veya Hisse Senedi olarak bulunamadı! "
        f"Geçerli örnekler: Kripto için (BTC, ETH, SOL, AVAX) | Hisseler için (NVDA, AAPL, TSLA, THYAO)."
    )


def generate_simulated_candles(symbol: str, asset_class: str) -> MarketData:
    sym = symbol.upper().strip()
    if asset_class == "CRYPTO":
        meta = COIN_CATALOGUE.get(sym, {"name": sym, "base_price": 100.0, "vol": 0.045})
        currency = "USD"
    else:
        meta = STOCK_CATALOGUE.get(sym, {"name": sym, "base_price": 150.0, "vol": 0.020, "currency": "USD"})
        currency = meta.get("currency", "USD")

    base_price = meta["base_price"]
    daily_vol = meta["vol"]

    rng = random.Random(hash(sym) & 0xFFFFFFFF)
    candles: list[Candle] = []
    current_price = base_price * (0.92 + (rng.random() * 0.16))
    now = datetime.now(timezone.utc)

    for i in range(60, 0, -1):
        dt = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        shock = rng.gauss(0.0004, daily_vol)
        open_p = current_price
        close_p = open_p * (1.0 + shock)
        high_p = max(open_p, close_p) * (1.0 + abs(rng.gauss(0, 0.008)))
        low_p = min(open_p, close_p) * (1.0 - abs(rng.gauss(0, 0.008)))
        vol = (base_price * 5000) * (0.7 + rng.random() * 0.6)

        candles.append(Candle(
            timestamp=dt,
            open=round(open_p, 4 if base_price < 1 else 2),
            high=round(high_p, 4 if base_price < 1 else 2),
            low=round(low_p, 4 if base_price < 1 else 2),
            close=round(close_p, 4 if base_price < 1 else 2),
            volume=round(vol, 2),
        ))
        current_price = close_p

    latest = candles[-1]
    prev_close = candles[-2].close if len(candles) >= 2 else latest.open
    pct_change = ((latest.close - prev_close) / prev_close) * 100.0

    indicators = compute_technical_indicators(candles)
    fg_score, fg_label = calculate_fear_and_greed(
        indicators.rsi_14, pct_change, indicators.trend_50_200, indicators.volume_ratio_24h
    )

    return MarketData(
        symbol=sym,
        asset_class=asset_class,
        current_price=latest.close,
        change_24h_pct=pct_change,
        high_24h=latest.high,
        low_24h=latest.low,
        volume_24h=latest.volume,
        currency=currency,
        candles=candles,
        indicators=indicators,
        fear_greed_score=fg_score,
        fear_greed_label=fg_label,
    )


def fetch_binance_crypto(symbol: str) -> MarketData | None:
    """Fetches real 24hr ticker & daily klines from public Binance API."""
    sym = symbol.upper().strip()
    pair = f"{sym}USDT"
    headers = {"User-Agent": "AlphaSwarm/1.0"}

    ticker_url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={pair}"
    klines_url = f"https://api.binance.com/api/v3/klines?symbol={pair}&interval=1d&limit=60"

    try:
        req_ticker = urllib.request.Request(ticker_url, headers=headers)
        with urllib.request.urlopen(req_ticker, timeout=4) as resp:
            ticker_json = json.loads(resp.read().decode())

        req_klines = urllib.request.Request(klines_url, headers=headers)
        with urllib.request.urlopen(req_klines, timeout=4) as resp:
            klines_json = json.loads(resp.read().decode())

        candles: list[Candle] = []
        for k in klines_json:
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
        pct_change = float(ticker_json["priceChangePercent"])
        fg_score, fg_label = calculate_fear_and_greed(
            indicators.rsi_14, pct_change, indicators.trend_50_200, indicators.volume_ratio_24h
        )

        return MarketData(
            symbol=sym,
            asset_class="CRYPTO",
            current_price=float(ticker_json["lastPrice"]),
            change_24h_pct=pct_change,
            high_24h=float(ticker_json["highPrice"]),
            low_24h=float(ticker_json["lowPrice"]),
            volume_24h=float(ticker_json["volume"]),
            currency="USD",
            candles=candles,
            indicators=indicators,
            fear_greed_score=fg_score,
            fear_greed_label=fg_label,
        )
    except Exception:
        return None


def fetch_yahoo_stock(symbol: str) -> MarketData | None:
    """Fetches real stock candles and price from Yahoo Finance."""
    sym = symbol.upper().strip()
    ticker = f"{sym}.IS" if sym in ("THYAO", "ASELS", "EREGL", "GARAN", "KCHOL") else sym
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=3mo"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())

        res = data["chart"]["result"][0]
        meta = res["meta"]
        quotes = res["indicators"]["quote"][0]
        timestamps = res["timestamp"]

        candles: list[Candle] = []
        for i in range(len(timestamps)):
            o = quotes["open"][i]
            h = quotes["high"][i]
            l = quotes["low"][i]
            c = quotes["close"][i]
            v = quotes["volume"][i] or 1000.0
            if None in (o, h, l, c):
                continue
            dt = datetime.fromtimestamp(timestamps[i], tz=timezone.utc).strftime("%Y-%m-%d")
            candles.append(Candle(
                timestamp=dt,
                open=round(float(o), 2),
                high=round(float(h), 2),
                low=round(float(l), 2),
                close=round(float(c), 2),
                volume=float(v),
            ))

        if len(candles) < 5:
            return None

        indicators = compute_technical_indicators(candles)
        last_price = float(meta.get("regularMarketPrice", candles[-1].close))
        prev_close = float(meta.get("previousClose", candles[-2].close if len(candles) >= 2 else last_price))
        pct_change = ((last_price - prev_close) / prev_close) * 100.0 if prev_close > 0 else 0.0

        fg_score, fg_label = calculate_fear_and_greed(
            indicators.rsi_14, pct_change, indicators.trend_50_200, indicators.volume_ratio_24h
        )

        return MarketData(
            symbol=sym,
            asset_class="EQUITY",
            current_price=last_price,
            change_24h_pct=pct_change,
            high_24h=max([c.high for c in candles[-5:]]),
            low_24h=min([c.low for c in candles[-5:]]),
            volume_24h=candles[-1].volume,
            currency=meta.get("currency", "TRY" if ".IS" in ticker else "USD"),
            candles=candles,
            indicators=indicators,
            fear_greed_score=fg_score,
            fear_greed_label=fg_label,
        )
    except Exception:
        return None


def get_market_data(symbol: str, asset_type: str | None = None, force_offline: bool = False) -> MarketData:
    """Validates symbol and returns MarketData. Throws ValueError on invalid symbol."""
    clean_sym, asset_class = validate_symbol(symbol, asset_type=asset_type)

    if not force_offline:
        if asset_class == "CRYPTO":
            live_crypto = fetch_binance_crypto(clean_sym)
            if live_crypto is not None:
                return live_crypto
        elif asset_class == "EQUITY":
            live_stock = fetch_yahoo_stock(clean_sym)
            if live_stock is not None:
                return live_stock

    return generate_simulated_candles(clean_sym, asset_class)


def get_top_assets(asset_type: str = "CRYPTO") -> list[dict]:
    catalog = COIN_CATALOGUE if asset_type == "CRYPTO" else STOCK_CATALOGUE
    items = []
    for sym, info in catalog.items():
        items.append({
            "symbol": sym,
            "name": info["name"],
            "asset_class": "CRYPTO" if asset_type == "CRYPTO" else "EQUITY",
            "currency": info.get("currency", "USD"),
        })
    return items
