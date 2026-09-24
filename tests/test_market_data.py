"""Unit tests for market data fetching, catalogs and validation."""

import pytest
from alphaswarm.market_data import generate_simulated_candles, get_market_data, validate_symbol


def test_mock_market_data_crypto():
    data = generate_simulated_candles("BTC", "CRYPTO")
    assert data.symbol == "BTC"
    assert data.asset_class == "CRYPTO"
    assert len(data.candles) == 60
    assert data.current_price > 0
    assert data.indicators is not None
    assert 0 <= data.indicators.rsi_14 <= 100


def test_mock_market_data_equity():
    data = generate_simulated_candles("NVDA", "EQUITY")
    assert data.symbol == "NVDA"
    assert data.asset_class == "EQUITY"
    assert len(data.candles) == 60
    assert data.current_price > 0


def test_get_market_data_offline():
    data = get_market_data("ETH", force_offline=True)
    assert data.symbol == "ETH"
    assert data.current_price > 0


def test_invalid_symbol_rejection():
    with pytest.raises(ValueError):
        validate_symbol("asdasd123random")

    with pytest.raises(ValueError):
        get_market_data("xyz999fake")
