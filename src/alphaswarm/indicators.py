"""Technical indicator computation engine using pure Python math."""

import math
from typing import Sequence
from alphaswarm.models import Candle, TechnicalIndicators


def calculate_sma(prices: Sequence[float], period: int) -> float:
    if not prices:
        return 0.0
    actual_period = min(len(prices), period)
    sub = prices[-actual_period:]
    return sum(sub) / actual_period


def calculate_ema(prices: Sequence[float], period: int) -> float:
    if not prices:
        return 0.0
    if len(prices) == 1:
        return prices[0]

    k = 2.0 / (period + 1)
    # Seed with SMA of the first slice
    seed_period = min(len(prices), period)
    ema = sum(prices[:seed_period]) / seed_period

    for price in prices[seed_period:]:
        ema = (price * k) + (ema * (1 - k))
    return ema


def calculate_rsi(prices: Sequence[float], period: int = 14) -> float:
    if len(prices) < 2:
        return 50.0

    gains = []
    losses = []
    for i in range(1, len(prices)):
        delta = prices[i] - prices[i - 1]
        if delta > 0:
            gains.append(delta)
            losses.append(0.0)
        else:
            gains.append(0.0)
            losses.append(abs(delta))

    if not gains:
        return 50.0

    actual_period = min(len(gains), period)
    # Initial averages
    avg_gain = sum(gains[:actual_period]) / actual_period
    avg_loss = sum(losses[:actual_period]) / actual_period

    # Wilder's smoothing
    for i in range(actual_period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0.0:
        return 100.0
    if avg_gain == 0.0:
        return 0.0

    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def calculate_macd(
    prices: Sequence[float], fast: int = 12, slow: int = 26, signal_period: int = 9
) -> tuple[float, float, float]:
    if len(prices) < 2:
        return 0.0, 0.0, 0.0

    # Calculate MACD series
    macd_series = []
    k_fast = 2.0 / (fast + 1)
    k_slow = 2.0 / (slow + 1)

    fast_ema = prices[0]
    slow_ema = prices[0]

    for p in prices:
        fast_ema = (p * k_fast) + (fast_ema * (1 - k_fast))
        slow_ema = (p * k_slow) + (slow_ema * (1 - k_slow))
        macd_series.append(fast_ema - slow_ema)

    macd_line = macd_series[-1]
    macd_signal = calculate_ema(macd_series, signal_period)
    macd_hist = macd_line - macd_signal

    return macd_line, macd_signal, macd_hist


def calculate_bollinger_bands(
    prices: Sequence[float], period: int = 20, num_std: float = 2.0
) -> tuple[float, float, float]:
    if not prices:
        return 0.0, 0.0, 0.0

    actual_period = min(len(prices), period)
    sub = prices[-actual_period:]
    mean = sum(sub) / actual_period

    if actual_period < 2:
        return mean, mean, mean

    variance = sum((x - mean) ** 2 for x in sub) / actual_period
    std = math.sqrt(variance)

    upper = mean + (num_std * std)
    lower = mean - (num_std * std)
    return upper, mean, lower


def calculate_atr(
    highs: Sequence[float], lows: Sequence[float], closes: Sequence[float], period: int = 14
) -> float:
    if len(closes) < 2:
        return (highs[-1] - lows[-1]) if highs and lows else 0.0

    tr_list = []
    for i in range(1, len(closes)):
        h = highs[i]
        l = lows[i]
        prev_c = closes[i - 1]
        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        tr_list.append(tr)

    return calculate_sma(tr_list, period)


def compute_technical_indicators(candles: list[Candle]) -> TechnicalIndicators:
    if not candles:
        return TechnicalIndicators(
            rsi_14=50.0,
            sma_20=0.0,
            sma_50=0.0,
            sma_200=0.0,
            macd_line=0.0,
            macd_signal=0.0,
            macd_hist=0.0,
            bollinger_upper=0.0,
            bollinger_middle=0.0,
            bollinger_lower=0.0,
            atr_14=0.0,
            volume_ratio_24h=1.0,
            trend_50_200="NEUTRAL",
        )

    closes = [c.close for c in candles]
    highs = [c.high for c in candles]
    lows = [c.low for c in candles]
    volumes = [c.volume for c in candles]

    rsi = calculate_rsi(closes, period=14)
    sma_20 = calculate_sma(closes, period=20)
    sma_50 = calculate_sma(closes, period=50)
    sma_200 = calculate_sma(closes, period=200)

    macd_line, macd_signal, macd_hist = calculate_macd(closes)
    bb_upper, bb_mid, bb_lower = calculate_bollinger_bands(closes, period=20)
    atr = calculate_atr(highs, lows, closes, period=14)

    # Volume ratio (current candle vs 20-period avg)
    avg_vol = calculate_sma(volumes, period=20)
    cur_vol = volumes[-1] if volumes else 1.0
    vol_ratio = (cur_vol / avg_vol) if avg_vol > 0 else 1.0

    # Trend 50 vs 200
    if sma_50 > sma_200 and closes[-1] > sma_50:
        trend = "BULLISH_STACK"
    elif sma_50 < sma_200 and closes[-1] < sma_50:
        trend = "BEARISH_STACK"
    elif sma_50 > sma_200:
        trend = "GOLDEN_CROSS"
    else:
        trend = "DEATH_CROSS"

    return TechnicalIndicators(
        rsi_14=rsi,
        sma_20=sma_20,
        sma_50=sma_50,
        sma_200=sma_200,
        macd_line=macd_line,
        macd_signal=macd_signal,
        macd_hist=macd_hist,
        bollinger_upper=bb_upper,
        bollinger_middle=bb_mid,
        bollinger_lower=bb_lower,
        atr_14=atr,
        volume_ratio_24h=vol_ratio,
        trend_50_200=trend,
    )
