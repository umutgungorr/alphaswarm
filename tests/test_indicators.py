"""Unit tests for technical indicator engine."""

from alphaswarm.indicators import (
    calculate_atr,
    calculate_bollinger_bands,
    calculate_ema,
    calculate_macd,
    calculate_rsi,
    calculate_sma,
    compute_technical_indicators,
)
from alphaswarm.models import Candle


def test_sma_and_ema():
    prices = [10.0, 11.0, 12.0, 13.0, 14.0]
    sma = calculate_sma(prices, 5)
    assert sma == 12.0

    ema = calculate_ema(prices, 5)
    assert 11.0 < ema < 14.0


def test_rsi_bounds():
    # Constant rising prices -> RSI should be high
    rising = [float(i) for i in range(1, 30)]
    rsi_high = calculate_rsi(rising, 14)
    assert rsi_high > 80.0

    # Constant falling prices -> RSI should be low
    falling = [float(30 - i) for i in range(1, 30)]
    rsi_low = calculate_rsi(falling, 14)
    assert rsi_low < 20.0


def test_bollinger_bands():
    prices = [100.0, 102.0, 98.0, 101.0, 99.0, 105.0, 95.0, 100.0]
    upper, mid, lower = calculate_bollinger_bands(prices, period=5)
    assert upper > mid > lower


def test_macd():
    prices = [float(100 + i * 2) for i in range(40)]
    macd_line, macd_signal, macd_hist = calculate_macd(prices)
    assert isinstance(macd_line, float)
    assert isinstance(macd_signal, float)
    assert isinstance(macd_hist, float)


def test_compute_technical_indicators():
    candles = [
        Candle(
            timestamp=f"2026-09-{i:02d}",
            open=100.0 + i,
            high=105.0 + i,
            low=95.0 + i,
            close=102.0 + i,
            volume=1000.0,
        )
        for i in range(1, 40)
    ]
    ind = compute_technical_indicators(candles)
    assert 0 <= ind.rsi_14 <= 100
    assert ind.sma_20 > 0
    assert ind.bollinger_upper >= ind.bollinger_lower
