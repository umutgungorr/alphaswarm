"""Specialized Autonomous Market Agents for AlphaSwarm."""

from alphaswarm.models import AgentRole, AgentThought, MarketData, Stance


class BaseAgent:
    def __init__(self, role: AgentRole, name: str, callsign: str):
        self.role = role
        self.name = name
        self.callsign = callsign

    def analyze(self, data: MarketData, previous_thoughts: list[AgentThought] | None = None) -> AgentThought:
        raise NotImplementedError


class TechnicalAnalystAgent(BaseAgent):
    def __init__(self):
        super().__init__(AgentRole.TECHNICAL, "Aria Vance", "QUANT-01")

    def analyze(self, data: MarketData, previous_thoughts: list[AgentThought] | None = None) -> AgentThought:
        ind = data.indicators
        price = data.current_price

        bullish_signals = 0
        bearish_signals = 0
        key_points = []
        risks = []

        # RSI Evaluation
        if ind.rsi_14 < 30:
            bullish_signals += 2
            key_points.append(f"RSI-14 ({ind.rsi_14:.1f}) indicates deeply oversold territory, mean-reversion bounce probable.")
        elif ind.rsi_14 > 70:
            bearish_signals += 2
            risks.append(f"RSI-14 ({ind.rsi_14:.1f}) signals overbought exhaustion; momentum stalling.")
        elif 50 <= ind.rsi_14 <= 65:
            bullish_signals += 1
            key_points.append(f"RSI-14 ({ind.rsi_14:.1f}) maintains healthy bullish continuation structure.")
        else:
            bearish_signals += 1
            key_points.append(f"RSI-14 ({ind.rsi_14:.1f}) shows sub-50 bearish weakness.")

        # Moving Averages & Trend Stack
        if ind.trend_50_200 == "BULLISH_STACK":
            bullish_signals += 2
            key_points.append(f"Strong Bullish Trend Stack: Price (${price:,.2f}) > SMA-50 (${ind.sma_50:,.2f}) > SMA-200 (${ind.sma_200:,.2f}).")
        elif ind.trend_50_200 == "BEARISH_STACK":
            bearish_signals += 2
            risks.append(f"Bearish Trend Stack: Price (${price:,.2f}) suppressed below SMA-50 (${ind.sma_50:,.2f}) and SMA-200 (${ind.sma_200:,.2f}).")
        elif ind.trend_50_200 == "GOLDEN_CROSS":
            bullish_signals += 2
            key_points.append("Recent 50/200 SMA Golden Cross confirmed on macro timeframe.")
        else:
            bearish_signals += 2
            risks.append("Recent 50/200 SMA Death Cross active.")

        # MACD
        if ind.macd_hist > 0:
            bullish_signals += 1
            key_points.append(f"MACD Histogram positive (+{ind.macd_hist:.4f}), expanding upward.")
        else:
            bearish_signals += 1
            risks.append(f"MACD Histogram negative ({ind.macd_hist:.4f}), bearish distribution active.")

        # Volume
        if ind.volume_ratio_24h > 1.3:
            key_points.append(f"Elevated volume expansion ({ind.volume_ratio_24h:.2f}x of 20-day mean) confirms directional commitment.")
        else:
            risks.append(f"Muted volume ({ind.volume_ratio_24h:.2f}x of 20-day mean) suggests low-conviction market drift.")

        # Determine Stance & Invalidation
        if bullish_signals >= bearish_signals + 3:
            stance = Stance.STRONG_BULL
            confidence = 0.85
            thesis = f"High-probability bullish expansion structure on {data.symbol}. Key indicators demonstrate clear momentum alignment."
            invalidation = ind.sma_50 * 0.97
        elif bullish_signals > bearish_signals:
            stance = Stance.BULLISH
            confidence = 0.68
            thesis = f"Constructive upward bias for {data.symbol}. Technical backdrop favors dip-buying toward upper Bollinger band (${ind.bollinger_upper:,.2f})."
            invalidation = ind.bollinger_middle * 0.98
        elif bearish_signals >= bullish_signals + 3:
            stance = Stance.STRONG_BEAR
            confidence = 0.85
            thesis = f"Aggressive structural breakdown underway for {data.symbol}. Critical supports failing with momentum confirmation."
            invalidation = ind.sma_50 * 1.03
        elif bearish_signals > bullish_signals:
            stance = Stance.BEARISH
            confidence = 0.65
            thesis = f"Vulnerable distribution pattern for {data.symbol}. Risk skewed toward testing lower Bollinger band (${ind.bollinger_lower:,.2f})."
            invalidation = ind.bollinger_middle * 1.02
        else:
            stance = Stance.NEUTRAL
            confidence = 0.50
            thesis = f"Compression regime for {data.symbol}. Indecisive market posture awaiting volatility breakout."
            invalidation = ind.bollinger_lower

        return AgentThought(
            role=self.role,
            agent_name=self.name,
            callsign=self.callsign,
            stance=stance,
            confidence=confidence,
            thesis=thesis,
            key_points=key_points,
            identified_risks=risks,
            suggested_invalidation=round(invalidation, 2),
        )


class SentimentAnalystAgent(BaseAgent):
    def __init__(self):
        super().__init__(AgentRole.SENTIMENT, "Marcus Cole", "MACRO-02")

    def analyze(self, data: MarketData, previous_thoughts: list[AgentThought] | None = None) -> AgentThought:
        tech_thought = next((t for t in (previous_thoughts or []) if t.role == AgentRole.TECHNICAL), None)
        price_change = data.change_24h_pct

        key_points = []
        risks = []

        if data.asset_class == "CRYPTO":
            if price_change > 2.0:
                key_points.append(f"Institutional net-inflow acceleration across digital asset ETPs; {data.symbol} liquidity depth expanding.")
                key_points.append("Options skew reflects strong call-side delta demand and short-squeeze positioning.")
                stance = Stance.BULLISH
                confidence = 0.72
                thesis = f"Macro liquidity and crypto-native narratives are providing strong tailwinds for {data.symbol}."
            elif price_change < -2.0:
                risks.append("Perpetual funding rates flipping negative; open interest flush-out underway.")
                risks.append("Macro regulatory uncertainty and treasury yield spikes creating defensive risk-off posture.")
                stance = Stance.BEARISH
                confidence = 0.70
                thesis = f"Macro headwinds and aggressive derisking pressure dominate near-term sentiment on {data.symbol}."
            else:
                key_points.append("Spot volume equilibrium observed; institutional accumulation absorbing local sell orders.")
                stance = Stance.NEUTRAL
                confidence = 0.55
                thesis = f"Sentiment remains neutral-to-cautious for {data.symbol}, pending catalyst announcement."
        else:
            # Equities
            if price_change >= 0.5:
                key_points.append(f"Earnings revision momentum and sector rotation favor {data.symbol}.")
                key_points.append("Implied volatility crush post-event confirms constructive institutional accumulation.")
                stance = Stance.BULLISH
                confidence = 0.75
                thesis = f"Fundamental multiples and enterprise demand trends justify multiple expansion on {data.symbol}."
            else:
                risks.append("Valuation multiples stretched against 10-year Treasury benchmark yields.")
                risks.append("Insider sales and defensive sector rotation signal near-term exhaustion.")
                stance = Stance.BEARISH
                confidence = 0.62
                thesis = f"Macro tightening and valuation sensitivity cap upside potential on {data.symbol}."

        # Cross-reference technical perspective if available
        if tech_thought and tech_thought.stance != stance:
            risks.append(f"Divergence detected: Sentiment ({stance.value}) conflicts with Technical Quant ({tech_thought.stance.value}).")

        return AgentThought(
            role=self.role,
            agent_name=self.name,
            callsign=self.callsign,
            stance=stance,
            confidence=confidence,
            thesis=thesis,
            key_points=key_points,
            identified_risks=risks,
        )


class RiskManagerAgent(BaseAgent):
    def __init__(self):
        super().__init__(AgentRole.RISK, "Vesper Sterling", "DEVIL-03")

    def analyze(self, data: MarketData, previous_thoughts: list[AgentThought] | None = None) -> AgentThought:
        tech = next((t for t in (previous_thoughts or []) if t.role == AgentRole.TECHNICAL), None)
        sent = next((t for t in (previous_thoughts or []) if t.role == AgentRole.SENTIMENT), None)

        ind = data.indicators
        key_points = []
        risks = []

        # The Risk Manager's explicit duty is to find failure modes and invalidation risks
        risks.append(f"ATR Volatility is ${ind.atr_14:,.2f}; unexpected whipsaw moves can trigger tight retail stops.")

        if ind.rsi_14 > 65:
            risks.append("Late-cycle long crowdedness: risk of cascading long liquidations if breakout fails.")
        elif ind.rsi_14 < 35:
            risks.append("Falling-knife dynamics: low liquidity support below current levels allows sudden air-pocket drops.")

        # Evaluate consensus alignment
        if tech and sent:
            if tech.stance == sent.stance and "BULL" in tech.stance.value:
                key_points.append("Dual confirmation between Technicals and Sentiment reduces asymmetric downside.")
                stance = Stance.BULLISH
                confidence = 0.65
                thesis = f"Bullish risk parameters are manageable with strict stop discipline on {data.symbol}."
                invalidation = data.current_price * 0.94
            elif tech.stance == sent.stance and "BEAR" in tech.stance.value:
                risks.append("High probability of multi-week drawdown; preserving capital is paramount.")
                stance = Stance.STRONG_BEAR
                confidence = 0.80
                thesis = f"Severe downside vulnerability on {data.symbol}; all long exposures should be hedged."
                invalidation = data.current_price * 1.05
            else:
                risks.append("Severe signal conflict between Technicals and Sentiment. Choppy whip-saw regime.")
                stance = Stance.NEUTRAL
                confidence = 0.75
                thesis = f"Risk/Reward profile is unacceptable for directional betting on {data.symbol}. Capital preservation advised."
                invalidation = data.current_price * 0.96
        else:
            stance = Stance.NEUTRAL
            confidence = 0.50
            thesis = "Insufficient cross-agent consensus for risk deployment."
            invalidation = data.current_price * 0.95

        return AgentThought(
            role=self.role,
            agent_name=self.name,
            callsign=self.callsign,
            stance=stance,
            confidence=confidence,
            thesis=thesis,
            key_points=key_points,
            identified_risks=risks,
            suggested_invalidation=round(invalidation, 2),
        )


class ArbitratorAgent(BaseAgent):
    def __init__(self):
        super().__init__(AgentRole.ARBITRATOR, "Sovereign AI", "CHIEF-CONSENSUS")

    def synthesize(
        self, data: MarketData, round_thoughts: list[AgentThought], round_num: int
    ) -> tuple[Stance, int, float, str, str, str]:
        """Synthesizes final verdict from round thoughts."""
        tech = next((t for t in round_thoughts if t.role == AgentRole.TECHNICAL), None)
        sent = next((t for t in round_thoughts if t.role == AgentRole.SENTIMENT), None)
        risk = next((t for t in round_thoughts if t.role == AgentRole.RISK), None)

        # Weighted score: Technical 40%, Sentiment 30%, Risk 30%
        weights = {
            Stance.STRONG_BULL: 2.0,
            Stance.BULLISH: 1.0,
            Stance.NEUTRAL: 0.0,
            Stance.BEARISH: -1.0,
            Stance.STRONG_BEAR: -2.0,
        }

        w_tech = weights.get(tech.stance if tech else Stance.NEUTRAL, 0.0) * 0.40
        w_sent = weights.get(sent.stance if sent else Stance.NEUTRAL, 0.0) * 0.30
        w_risk = weights.get(risk.stance if risk else Stance.NEUTRAL, 0.0) * 0.30

        total_score = w_tech + w_sent + w_risk

        if total_score >= 1.2:
            final_stance = Stance.STRONG_BULL
            conf = int(min(95, 75 + total_score * 10))
        elif total_score >= 0.35:
            final_stance = Stance.BULLISH
            conf = int(min(85, 60 + total_score * 15))
        elif total_score <= -1.2:
            final_stance = Stance.STRONG_BEAR
            conf = int(min(95, 75 + abs(total_score) * 10))
        elif total_score <= -0.35:
            final_stance = Stance.BEARISH
            conf = int(min(85, 60 + abs(total_score) * 15))
        else:
            final_stance = Stance.NEUTRAL
            conf = 50

        # Invalidation
        invalidation = risk.suggested_invalidation if (risk and risk.suggested_invalidation) else (data.current_price * 0.95)

        # Synthesize thesis
        thesis = (
            f"Consensus Swarm settles on {final_stance.value} for {data.symbol} (${data.current_price:,.2f}) "
            f"with {conf}% weighted conviction. "
            f"Technical momentum ({tech.stance.value if tech else 'N/A'}) meets Risk Assessment ({risk.stance.value if risk else 'N/A'})."
        )

        bull_case = tech.thesis if tech else "Technical trend momentum"
        bear_case = (risk.identified_risks[0] if risk and risk.identified_risks else "Macro drawdown risk")

        return final_stance, conf, invalidation, thesis, bull_case, bear_case
