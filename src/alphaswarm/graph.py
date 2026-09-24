"""Multi-Agent Consensus Graph Execution Engine."""

from typing import Callable, Optional
from alphaswarm.agents import ArbitratorAgent, RiskManagerAgent, SentimentAnalystAgent, TechnicalAnalystAgent
from alphaswarm.models import AgentThought, ConsensusVerdict, DebateRound, MarketData, Stance


class AlphaSwarmGraph:
    def __init__(self, max_rounds: int = 1):
        self.max_rounds = max(1, min(max_rounds, 3))
        self.technical_agent = TechnicalAnalystAgent()
        self.sentiment_agent = SentimentAnalystAgent()
        self.risk_agent = RiskManagerAgent()
        self.arbitrator = ArbitratorAgent()

    def propagate(
        self,
        market_data: MarketData,
        on_agent_speak: Optional[Callable[[AgentThought, int], None]] = None,
        on_round_start: Optional[Callable[[int], None]] = None,
        lang: str = "tr",
    ) -> ConsensusVerdict:
        """Executes the multi-agent consensus graph over N debate rounds."""
        rounds: list[DebateRound] = []
        accumulated_thoughts: list[AgentThought] = []

        for r in range(1, self.max_rounds + 1):
            if on_round_start:
                on_round_start(r)

            current_round_thoughts: list[AgentThought] = []

            # 1. Technical Analyst
            tech_thought = self.technical_agent.analyze(market_data, accumulated_thoughts, lang=lang)
            current_round_thoughts.append(tech_thought)
            if on_agent_speak:
                on_agent_speak(tech_thought, r)

            # 2. Sentiment Analyst
            sent_thought = self.sentiment_agent.analyze(market_data, current_round_thoughts, lang=lang)
            current_round_thoughts.append(sent_thought)
            if on_agent_speak:
                on_agent_speak(sent_thought, r)

            # 3. Risk Manager (Devil's Advocate)
            risk_thought = self.risk_agent.analyze(market_data, current_round_thoughts, lang=lang)
            current_round_thoughts.append(risk_thought)
            if on_agent_speak:
                on_agent_speak(risk_thought, r)

            accumulated_thoughts.extend(current_round_thoughts)

            # Note shifts if round > 1
            if lang == "tr":
                shift_note = "Başlangıç tezleri ve konumlanmalar belirlendi." if r == 1 else "Karşıt argümanlar değerlendirildi; güven sınırları daraltıldı."
            else:
                shift_note = "Initial positioning established." if r == 1 else "Cross-agent counterarguments integrated; confidence bands tightened."

            rounds.append(DebateRound(
                round_number=r,
                thoughts=current_round_thoughts,
                consensus_shift_notes=shift_note,
            ))

        # 4. Final Arbitrator Consensus
        final_stance, confidence, invalidation, thesis, bull_case, bear_case = self.arbitrator.synthesize(
            market_data, rounds[-1].thoughts, len(rounds), lang=lang
        )

        # 5. Derive actionable execution parameters (Targets, Support, Resistance, R:R)
        price = market_data.current_price
        ind = market_data.indicators
        atr = ind.atr_14 if (ind and ind.atr_14 > 0) else (price * 0.03)

        if final_stance in (Stance.STRONG_BULL, Stance.BULLISH):
            tp1 = round(max(price + atr * 1.5, ind.bollinger_upper if (ind and ind.bollinger_upper > price) else price * 1.05), 2)
            tp2 = round(price + atr * 3.2, 2)
            risk = max(price * 0.005, abs(price - invalidation))
            reward = max(price * 0.005, tp1 - price)
            rr = round(reward / risk, 2)
            support = round(min(ind.bollinger_lower if ind else price * 0.95, invalidation), 2)
            resistance = round(tp1, 2)
        elif final_stance in (Stance.STRONG_BEAR, Stance.BEARISH):
            tp1 = round(min(price - atr * 1.5, ind.bollinger_lower if (ind and ind.bollinger_lower < price) else price * 0.95), 2)
            tp2 = round(max(0.01, price - atr * 3.2), 2)
            risk = max(price * 0.005, abs(invalidation - price))
            reward = max(price * 0.005, price - tp1)
            rr = round(reward / risk, 2)
            support = round(tp1, 2)
            resistance = round(max(ind.bollinger_upper if ind else price * 1.05, invalidation), 2)
        else:
            support = round(ind.bollinger_lower if (ind and ind.bollinger_lower > 0) else price * 0.96, 2)
            resistance = round(ind.bollinger_upper if (ind and ind.bollinger_upper > 0) else price * 1.04, 2)
            tp1 = round(resistance, 2)
            tp2 = round(resistance * 1.03, 2)
            rr = 1.0

        return ConsensusVerdict(
            symbol=market_data.symbol,
            final_stance=final_stance,
            confidence_score=confidence,
            market_price=market_data.current_price,
            time_horizon="SWING_1_TO_4_WEEKS",
            key_invalidation_level=invalidation,
            take_profit_1=tp1,
            take_profit_2=tp2,
            risk_reward_ratio=rr,
            support_level=support,
            resistance_level=resistance,
            primary_thesis=thesis,
            bull_case=bull_case,
            bear_case=bear_case,
            debate_rounds=rounds,
        )
