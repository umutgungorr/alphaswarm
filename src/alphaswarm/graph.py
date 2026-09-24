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
    ) -> ConsensusVerdict:
        """Executes the multi-agent consensus graph over N debate rounds."""
        rounds: list[DebateRound] = []
        accumulated_thoughts: list[AgentThought] = []

        for r in range(1, self.max_rounds + 1):
            if on_round_start:
                on_round_start(r)

            current_round_thoughts: list[AgentThought] = []

            # 1. Technical Analyst
            tech_thought = self.technical_agent.analyze(market_data, accumulated_thoughts)
            current_round_thoughts.append(tech_thought)
            if on_agent_speak:
                on_agent_speak(tech_thought, r)

            # 2. Sentiment Analyst
            sent_thought = self.sentiment_agent.analyze(market_data, current_round_thoughts)
            current_round_thoughts.append(sent_thought)
            if on_agent_speak:
                on_agent_speak(sent_thought, r)

            # 3. Risk Manager (Devil's Advocate)
            risk_thought = self.risk_agent.analyze(market_data, current_round_thoughts)
            current_round_thoughts.append(risk_thought)
            if on_agent_speak:
                on_agent_speak(risk_thought, r)

            accumulated_thoughts.extend(current_round_thoughts)

            # Note shifts if round > 1
            shift_note = "Initial positioning established."
            if r > 1:
                shift_note = "Cross-agent counterarguments integrated; confidence bands tightened."

            rounds.append(DebateRound(
                round_number=r,
                thoughts=current_round_thoughts,
                consensus_shift_notes=shift_note,
            ))

        # 4. Final Arbitrator Consensus
        final_stance, confidence, invalidation, thesis, bull_case, bear_case = self.arbitrator.synthesize(
            market_data, rounds[-1].thoughts, len(rounds)
        )

        return ConsensusVerdict(
            symbol=market_data.symbol,
            final_stance=final_stance,
            confidence_score=confidence,
            market_price=market_data.current_price,
            time_horizon="SWING_1_TO_4_WEEKS",
            key_invalidation_level=invalidation,
            primary_thesis=thesis,
            bull_case=bull_case,
            bear_case=bear_case,
            debate_rounds=rounds,
        )
