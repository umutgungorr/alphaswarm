"""Unit tests for market data fetching and simulation."""

from alphaswarm.market_data import generate_mock_market_data, get_market_data


def test_mock_market_data_crypto():
    data = generate_mock_market_data("BTC")
    assert data.symbol == "BTC"
    assert data.asset_class == "CRYPTO"
    assert len(data.candles) == 60
    assert data.current_price > 0
    assert data.indicators is not None
    assert 0 <= data.indicators.rsi_14 <= 100


def test_mock_market_data_equity():
    data = generate_mock_market_data("NVDA")
    assert data.symbol == "NVDA"
    assert data.asset_class == "EQUITY"
    assert len(data.candles) == 60
    assert data.current_price > 0


def test_get_market_data_offline():
    data = get_market_data("ETH", force_offline=True)
    assert data.symbol == "ETH"
    assert data.current_price > 0
