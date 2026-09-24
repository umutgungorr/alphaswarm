"""Unit tests for AlphaSwarm consensus graph."""

from alphaswarm.graph import AlphaSwarmGraph
from alphaswarm.market_data import get_market_data


def test_graph_propagation():
    data = get_market_data("SOL", force_offline=True)
    graph = AlphaSwarmGraph(max_rounds=2)

    spoken_thoughts = []

    def on_speak(thought, r):
        spoken_thoughts.append((thought.callsign, r))

    verdict = graph.propagate(data, on_agent_speak=on_speak)

    assert verdict.symbol == "SOL"
    assert 0 <= verdict.confidence_score <= 100
    assert len(verdict.debate_rounds) == 2
    # 3 agents per round * 2 rounds = 6 speeches
    assert len(spoken_thoughts) == 6
    assert verdict.primary_thesis != ""
    assert verdict.key_invalidation_level > 0
    assert verdict.take_profit_1 > 0
    assert verdict.take_profit_2 > 0
    assert verdict.risk_reward_ratio > 0
    assert verdict.support_level > 0
    assert verdict.resistance_level > 0
