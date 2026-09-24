"""Unit tests for specialized market agents."""

from alphaswarm.agents import ArbitratorAgent, RiskManagerAgent, SentimentAnalystAgent, TechnicalAnalystAgent
from alphaswarm.market_data import get_market_data
from alphaswarm.models import AgentRole


def test_agent_roles_and_analysis():
    data = get_market_data("BTC", force_offline=True)

    tech_agent = TechnicalAnalystAgent()
    tech_thought = tech_agent.analyze(data)
    assert tech_thought.role == AgentRole.TECHNICAL
    assert tech_thought.confidence > 0
    assert len(tech_thought.key_points) > 0

    sent_agent = SentimentAnalystAgent()
    sent_thought = sent_agent.analyze(data, [tech_thought])
    assert sent_thought.role == AgentRole.SENTIMENT
    assert sent_thought.thesis != ""

    risk_agent = RiskManagerAgent()
    risk_thought = risk_agent.analyze(data, [tech_thought, sent_thought])
    assert risk_thought.role == AgentRole.RISK
    assert len(risk_thought.identified_risks) > 0

    arbitrator = ArbitratorAgent()
    verdict_stance, conf, inval, thesis_tr, bull, bear = arbitrator.synthesize(
        data, [tech_thought, sent_thought, risk_thought], round_num=1, lang="tr"
    )
    assert 0 <= conf <= 100
    assert inval > 0
    assert "Konsensüs Swarm" in thesis_tr

    _, _, _, thesis_en, _, _ = arbitrator.synthesize(
        data, [tech_thought, sent_thought, risk_thought], round_num=1, lang="en"
    )
    assert "Consensus Swarm settles on" in thesis_en
