"""Core data models for AlphaSwarm Multi-Agent Intelligence Hub."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class Stance(str, Enum):
    STRONG_BULL = "STRONG_BULL"
    BULLISH = "BULLISH"
    NEUTRAL = "NEUTRAL"
    BEARISH = "BEARISH"
    STRONG_BEAR = "STRONG_BEAR"


class AgentRole(str, Enum):
    TECHNICAL = "TECHNICAL"
    SENTIMENT = "SENTIMENT"
    RISK = "RISK"
    ARBITRATOR = "ARBITRATOR"


@dataclass
class Candle:
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "open": round(self.open, 4 if self.open < 1 else 2),
            "high": round(self.high, 4 if self.high < 1 else 2),
            "low": round(self.low, 4 if self.low < 1 else 2),
            "close": round(self.close, 4 if self.close < 1 else 2),
            "volume": round(self.volume, 2),
        }


@dataclass
class TechnicalIndicators:
    rsi_14: float
    sma_20: float
    sma_50: float
    sma_200: float
    macd_line: float
    macd_signal: float
    macd_hist: float
    bollinger_upper: float
    bollinger_middle: float
    bollinger_lower: float
    atr_14: float
    volume_ratio_24h: float  # current volume vs 20-period avg
    trend_50_200: str  # "GOLDEN_CROSS", "DEATH_CROSS", "BULLISH_STACK", "BEARISH_STACK"

    def to_dict(self) -> dict[str, Any]:
        return {
            "rsi_14": round(self.rsi_14, 2),
            "sma_20": round(self.sma_20, 2),
            "sma_50": round(self.sma_50, 2),
            "sma_200": round(self.sma_200, 2),
            "macd_line": round(self.macd_line, 4),
            "macd_signal": round(self.macd_signal, 4),
            "macd_hist": round(self.macd_hist, 4),
            "bollinger_upper": round(self.bollinger_upper, 2),
            "bollinger_middle": round(self.bollinger_middle, 2),
            "bollinger_lower": round(self.bollinger_lower, 2),
            "atr_14": round(self.atr_14, 2),
            "volume_ratio_24h": round(self.volume_ratio_24h, 2),
            "trend_50_200": self.trend_50_200,
        }


@dataclass
class MarketData:
    symbol: str
    asset_class: str  # "CRYPTO", "EQUITY", "COMMODITY"
    current_price: float
    change_24h_pct: float
    high_24h: float
    low_24h: float
    volume_24h: float
    currency: str = "USD"
    candles: list[Candle] = field(default_factory=list)
    indicators: Optional[TechnicalIndicators] = None
    fear_greed_score: int = 50
    fear_greed_label: str = "NEUTRAL"

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "asset_class": self.asset_class,
            "current_price": self.current_price,
            "change_24h_pct": round(self.change_24h_pct, 2),
            "high_24h": self.high_24h,
            "low_24h": self.low_24h,
            "volume_24h": self.volume_24h,
            "currency": self.currency,
            "fear_greed_score": self.fear_greed_score,
            "fear_greed_label": self.fear_greed_label,
            "indicators": self.indicators.to_dict() if self.indicators else None,
            "candles": [c.to_dict() for c in self.candles[-45:]],
        }


@dataclass
class AgentThought:
    role: AgentRole
    agent_name: str
    callsign: str
    stance: Stance
    confidence: float  # 0.0 to 1.0
    thesis: str
    key_points: list[str]
    identified_risks: list[str]
    suggested_invalidation: Optional[float] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role.value,
            "agent_name": self.agent_name,
            "callsign": self.callsign,
            "stance": self.stance.value,
            "confidence": round(self.confidence, 2),
            "thesis": self.thesis,
            "key_points": self.key_points,
            "identified_risks": self.identified_risks,
            "suggested_invalidation": self.suggested_invalidation,
        }


@dataclass
class DebateRound:
    round_number: int
    thoughts: list[AgentThought]
    consensus_shift_notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "round_number": self.round_number,
            "thoughts": [t.to_dict() for t in self.thoughts],
            "consensus_shift_notes": self.consensus_shift_notes,
        }


@dataclass
class ConsensusVerdict:
    symbol: str
    final_stance: Stance
    confidence_score: int  # 0 to 100
    market_price: float
    time_horizon: str  # "SWING_1_TO_4_WEEKS", "INTRADAY", "POSITION"
    key_invalidation_level: float
    primary_thesis: str
    bull_case: str
    bear_case: str
    debate_rounds: list[DebateRound]
    take_profit_1: float = 0.0
    take_profit_2: float = 0.0
    risk_reward_ratio: float = 0.0
    support_level: float = 0.0
    resistance_level: float = 0.0
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "final_stance": self.final_stance.value,
            "confidence_score": self.confidence_score,
            "market_price": self.market_price,
            "time_horizon": self.time_horizon,
            "key_invalidation_level": self.key_invalidation_level,
            "take_profit_1": self.take_profit_1,
            "take_profit_2": self.take_profit_2,
            "risk_reward_ratio": self.risk_reward_ratio,
            "support_level": self.support_level,
            "resistance_level": self.resistance_level,
            "primary_thesis": self.primary_thesis,
            "bull_case": self.bull_case,
            "bear_case": self.bear_case,
            "debate_rounds": [r.to_dict() for r in self.debate_rounds],
            "generated_at": self.generated_at,
        }
