"""Specialized Autonomous Market Agents for AlphaSwarm with full TR/EN bilingual support."""

from alphaswarm.models import AgentRole, AgentThought, MarketData, Stance


STANCE_TR = {
    Stance.STRONG_BULL: "GÜÇLÜ YÜKSELİŞ",
    Stance.BULLISH: "YÜKSELİŞ",
    Stance.NEUTRAL: "NÖTR / KARARSIZ",
    Stance.BEARISH: "DÜŞÜŞ",
    Stance.STRONG_BEAR: "GÜÇLÜ DÜŞÜŞ",
}


class BaseAgent:
    def __init__(self, role: AgentRole, name_en: str, name_tr: str, callsign: str):
        self.role = role
        self.name_en = name_en
        self.name_tr = name_tr
        self.callsign = callsign

    def get_name(self, lang: str = "tr") -> str:
        return self.name_tr if lang == "tr" else self.name_en

    def analyze(self, data: MarketData, previous_thoughts: list[AgentThought] | None = None, lang: str = "tr") -> AgentThought:
        raise NotImplementedError


class TechnicalAnalystAgent(BaseAgent):
    def __init__(self):
        super().__init__(AgentRole.TECHNICAL, "Aria Vance", "Aria Vance (Kantitatif / Teknik Analist)", "QUANT-01")

    def analyze(self, data: MarketData, previous_thoughts: list[AgentThought] | None = None, lang: str = "tr") -> AgentThought:
        ind = data.indicators
        price = data.current_price
        c_sym = data.currency

        bullish_signals = 0
        bearish_signals = 0
        key_points = []
        risks = []

        if lang == "tr":
            # RSI
            if ind.rsi_14 < 30:
                bullish_signals += 2
                key_points.append(f"RSI-14 ({ind.rsi_14:.1f}) aşırı satım bölgesinde (<30); teknik tepki sıçraması bekleniyor.")
            elif ind.rsi_14 > 70:
                bearish_signals += 2
                risks.append(f"RSI-14 ({ind.rsi_14:.1f}) aşırı alım bölgesinde (>70); yukarı yönlü momentum yoruluyor.")
            elif 50 <= ind.rsi_14 <= 65:
                bullish_signals += 1
                key_points.append(f"RSI-14 ({ind.rsi_14:.1f}) sağlıklı yükseliş devam yapısını koruyor.")
            else:
                bearish_signals += 1
                key_points.append(f"RSI-14 ({ind.rsi_14:.1f}) 50 seviyesi altında zayıf satıcılı seyir gösteriyor.")

            # Trend & Moving Averages
            if ind.trend_50_200 == "BULLISH_STACK":
                bullish_signals += 2
                key_points.append(f"Güçlü Yükseliş Trend Dizilimi: Fiyat ({price:,.2f} {c_sym}) > SMA-50 ({ind.sma_50:,.2f}) > SMA-200 ({ind.sma_200:,.2f}).")
            elif ind.trend_50_200 == "BEARISH_STACK":
                bearish_signals += 2
                risks.append(f"Düşüş Trend Baskısı: Fiyat ({price:,.2f} {c_sym}) hem 50 hem de 200 günlük hareketli ortalamanın altında.")
            elif ind.trend_50_200 == "GOLDEN_CROSS":
                bullish_signals += 2
                key_points.append("50/200 Günlük SMA Altın Kesişim (Golden Cross) makro zaman diliminde onaylandı.")
            else:
                bearish_signals += 2
                risks.append("50/200 Günlük SMA Ölüm Kesişimi (Death Cross) aktif baskı yaratıyor.")

            # MACD
            if ind.macd_hist > 0:
                bullish_signals += 1
                key_points.append(f"MACD Histogramı pozitif (+{ind.macd_hist:.4f}), momentum genişliyor.")
            else:
                bearish_signals += 1
                risks.append(f"MACD Histogramı negatif ({ind.macd_hist:.4f}), satış baskısı devam ediyor.")

            # Volume
            if ind.volume_ratio_24h > 1.3:
                key_points.append(f"İşlem hacmi 20 günlük ortalamanın {ind.volume_ratio_24h:.2f} katına çıktı; yönelim kararlılığı güçlü.")
            else:
                risks.append(f"Düşük işlem hacmi ({ind.volume_ratio_24h:.2f}x ortalama) piyasada hacimsiz sürüklenmeye işaret ediyor.")

            if bullish_signals >= bearish_signals + 3:
                stance = Stance.STRONG_BULL
                confidence = 0.85
                thesis = f"{data.symbol} üzerinde yüksek olasılıklı teknik yükseliş kırılımı gözlemleniyor. Momentum göstergeleri tam uyumlu."
                invalidation = ind.sma_50 * 0.97
            elif bullish_signals > bearish_signals:
                stance = Stance.BULLISH
                confidence = 0.68
                thesis = f"{data.symbol} için yukarı yönlü yapı korunuyor. Geri çekilmelerde üst Bollinger bandı ({ind.bollinger_upper:,.2f}) hedeflenebilir."
                invalidation = ind.bollinger_middle * 0.98
            elif bearish_signals >= bullish_signals + 3:
                stance = Stance.STRONG_BEAR
                confidence = 0.85
                thesis = f"{data.symbol} üzerinde sert yapısal kırılma devam ediyor. Kritik destekler satış hacmiyle kaybedildi."
                invalidation = ind.sma_50 * 1.03
            elif bearish_signals > bullish_signals:
                stance = Stance.BEARISH
                confidence = 0.65
                thesis = f"{data.symbol} için dağıtım paterni aktif. Fiyatın alt Bollinger bandını ({ind.bollinger_lower:,.2f}) test etme riski yüksek."
                invalidation = ind.bollinger_middle * 1.02
            else:
                stance = Stance.NEUTRAL
                confidence = 0.50
                thesis = f"{data.symbol} fiyat sıkışması ve bant daralması içinde. Yön tayini için kırılım beklenmeli."
                invalidation = ind.bollinger_lower
        else:
            # English implementation
            if ind.rsi_14 < 30:
                bullish_signals += 2
                key_points.append(f"RSI-14 ({ind.rsi_14:.1f}) indicates deeply oversold territory, mean-reversion probable.")
            elif ind.rsi_14 > 70:
                bearish_signals += 2
                risks.append(f"RSI-14 ({ind.rsi_14:.1f}) signals overbought exhaustion; momentum stalling.")
            elif 50 <= ind.rsi_14 <= 65:
                bullish_signals += 1
                key_points.append(f"RSI-14 ({ind.rsi_14:.1f}) maintains healthy bullish continuation structure.")
            else:
                bearish_signals += 1
                key_points.append(f"RSI-14 ({ind.rsi_14:.1f}) shows sub-50 bearish weakness.")

            if ind.trend_50_200 == "BULLISH_STACK":
                bullish_signals += 2
                key_points.append(f"Bullish Trend Stack: Price (${price:,.2f}) > SMA-50 (${ind.sma_50:,.2f}) > SMA-200 (${ind.sma_200:,.2f}).")
            elif ind.trend_50_200 == "BEARISH_STACK":
                bearish_signals += 2
                risks.append(f"Bearish Trend Stack: Price (${price:,.2f}) suppressed below SMA-50 and SMA-200.")
            elif ind.trend_50_200 == "GOLDEN_CROSS":
                bullish_signals += 2
                key_points.append("Macro 50/200 SMA Golden Cross confirmed.")
            else:
                bearish_signals += 2
                risks.append("Macro 50/200 SMA Death Cross active.")

            if ind.macd_hist > 0:
                bullish_signals += 1
                key_points.append(f"MACD Histogram positive (+{ind.macd_hist:.4f}), expanding upward.")
            else:
                bearish_signals += 1
                risks.append(f"MACD Histogram negative ({ind.macd_hist:.4f}), distribution active.")

            if ind.volume_ratio_24h > 1.3:
                key_points.append(f"Volume expansion ({ind.volume_ratio_24h:.2f}x of 20-day mean) confirms directional commitment.")
            else:
                risks.append(f"Muted volume ({ind.volume_ratio_24h:.2f}x mean) suggests low-conviction drift.")

            if bullish_signals >= bearish_signals + 3:
                stance = Stance.STRONG_BULL
                confidence = 0.85
                thesis = f"High-probability bullish expansion structure on {data.symbol}. Momentum signals aligned."
                invalidation = ind.sma_50 * 0.97
            elif bullish_signals > bearish_signals:
                stance = Stance.BULLISH
                confidence = 0.68
                thesis = f"Constructive upward bias for {data.symbol}. Technical backdrop favors dip-buying toward upper Bollinger band."
                invalidation = ind.bollinger_middle * 0.98
            elif bearish_signals >= bullish_signals + 3:
                stance = Stance.STRONG_BEAR
                confidence = 0.85
                thesis = f"Aggressive structural breakdown underway for {data.symbol}. Critical supports failing."
                invalidation = ind.sma_50 * 1.03
            elif bearish_signals > bullish_signals:
                stance = Stance.BEARISH
                confidence = 0.65
                thesis = f"Vulnerable distribution pattern for {data.symbol}. Testing lower Bollinger band is probable."
                invalidation = ind.bollinger_middle * 1.02
            else:
                stance = Stance.NEUTRAL
                confidence = 0.50
                thesis = f"Compression regime for {data.symbol}. Awaiting breakout."
                invalidation = ind.bollinger_lower

        return AgentThought(
            role=self.role,
            agent_name=self.get_name(lang),
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
        super().__init__(AgentRole.SENTIMENT, "Marcus Cole", "Marcus Cole (Haber & Makro Duyarlılık)", "MACRO-02")

    def analyze(self, data: MarketData, previous_thoughts: list[AgentThought] | None = None, lang: str = "tr") -> AgentThought:
        tech_thought = next((t for t in (previous_thoughts or []) if t.role == AgentRole.TECHNICAL), None)
        price_change = data.change_24h_pct

        key_points = []
        risks = []

        if lang == "tr":
            if data.asset_class == "CRYPTO":
                if price_change > 1.5:
                    key_points.append(f"Kurumsal fon girişleri ve borsa dışı (OTC) cüzdan birikimleri {data.symbol} derinliğini destekliyor.")
                    key_points.append("Türev piyasasında long delta talebi ve pozitif fonlama faizi yükseliş iştahını yansıtıyor.")
                    stance = Stance.BULLISH
                    confidence = 0.72
                    thesis = f"Makro likidite akımları ve kripto yerel anlatıları {data.symbol} için güçlü arkadan esen rüzgarlar sağlıyor."
                elif price_change < -1.5:
                    risks.append("Sürekli sözleşmelerde (perpetuals) fonlama negatifleşiyor; kaldıraç tasfiyesi hızlandı.")
                    risks.append("Makro faiz beklentileri ve regülasyon belirsizliği riskten kaçış (risk-off) baskısı yaratıyor.")
                    stance = Stance.BEARISH
                    confidence = 0.70
                    thesis = f"Kısa vadede makro karşı rüzgarlar ve riskten kaçış satışları {data.symbol} üzerinde hakim."
                else:
                    key_points.append("Spot hacim dengesi korunuyor; kurumsal emirler taban seviyelerde likidite topluyor.")
                    stance = Stance.NEUTRAL
                    confidence = 0.55
                    thesis = f"{data.symbol} için piyasa hissiyatı dengeli-temkinli seyrediyor; yeni katalizör bekleniyor."
            else:
                # Equity TR
                if price_change >= 0.3:
                    key_points.append(f"Sektörel rotasyon ve bilanço beklentileri {data.symbol} paylarına kurumsal talep çekiyor.")
                    key_points.append("Opsiyon oynaklık daralması (IV crush) kurumsal birikim sürecini teyit ediyor.")
                    stance = Stance.BULLISH
                    confidence = 0.75
                    thesis = f"Temel büyüme çarpanları ve sektör liderliği {data.symbol} için çarpan genişlemesini haklı çıkarıyor."
                else:
                    risks.append("Şirket değerlemeleri tahvil getirisi karşısında primli görünüyor.")
                    risks.append("Savunmacı sektörlere geçiş ve tepe fiyat kar realizasyonu gözlemleniyor.")
                    stance = Stance.BEARISH
                    confidence = 0.62
                    thesis = f"Makro sıkılaşma ve faiz hassasiyeti {data.symbol} üzerindeki tepe potansiyelini sınırlıyor."

            if tech_thought and tech_thought.stance != stance:
                risks.append(f"Uyumsuzluk (Divergence): Duyarlılık ({STANCE_TR.get(stance)}) ile Teknik Analist ({STANCE_TR.get(tech_thought.stance)}) çelişiyor.")
        else:
            # English
            if data.asset_class == "CRYPTO":
                if price_change > 1.5:
                    key_points.append(f"Institutional net-inflows and ETP allocations expanding {data.symbol} order book depth.")
                    stance = Stance.BULLISH
                    confidence = 0.72
                    thesis = f"Macro liquidity and crypto-native narratives are providing strong tailwinds for {data.symbol}."
                elif price_change < -1.5:
                    risks.append("Perpetual funding flipping negative; leverage liquidation active.")
                    stance = Stance.BEARISH
                    confidence = 0.70
                    thesis = f"Macro headwinds and derisking pressure dominate near-term sentiment on {data.symbol}."
                else:
                    key_points.append("Spot volume equilibrium observed; institutional accumulation absorbing orders.")
                    stance = Stance.NEUTRAL
                    confidence = 0.55
                    thesis = f"Sentiment remains neutral-to-cautious for {data.symbol}."
            else:
                if price_change >= 0.3:
                    key_points.append(f"Earnings revision momentum and sector rotation favor {data.symbol}.")
                    stance = Stance.BULLISH
                    confidence = 0.75
                    thesis = f"Enterprise demand trends justify multiple expansion on {data.symbol}."
                else:
                    risks.append("Valuation multiples stretched against benchmark bond yields.")
                    stance = Stance.BEARISH
                    confidence = 0.62
                    thesis = f"Macro tightening caps upside potential on {data.symbol}."

        return AgentThought(
            role=self.role,
            agent_name=self.get_name(lang),
            callsign=self.callsign,
            stance=stance,
            confidence=confidence,
            thesis=thesis,
            key_points=key_points,
            identified_risks=risks,
        )


class RiskManagerAgent(BaseAgent):
    def __init__(self):
        super().__init__(AgentRole.RISK, "Vesper Sterling", "Vesper Sterling (Risk Yöneticisi & Şeytanın Avukatı)", "DEVIL-03")

    def analyze(self, data: MarketData, previous_thoughts: list[AgentThought] | None = None, lang: str = "tr") -> AgentThought:
        tech = next((t for t in (previous_thoughts or []) if t.role == AgentRole.TECHNICAL), None)
        sent = next((t for t in (previous_thoughts or []) if t.role == AgentRole.SENTIMENT), None)

        ind = data.indicators
        key_points = []
        risks = []
        c_sym = data.currency

        if lang == "tr":
            risks.append(f"ATR Volatilitesi {ind.atr_14:,.2f} {c_sym}; beklenmedik ani iğneler dar stopları patlatabilir.")

            if ind.rsi_14 > 65:
                risks.append("Aşırı kalabalık long pozisyonları: Olası kırılım başarısızlığında zincirleme tasfiye riski var.")
            elif ind.rsi_14 < 35:
                risks.append("Düşen bıçak dinamikleri: Fiyatın altında zayıf likidite desteği ani boşluklu düşüşlere yol açabilir.")

            if tech and sent:
                if tech.stance == sent.stance and "BULL" in tech.stance.value:
                    key_points.append("Teknik ve Temel analiz uyumu asimetrik aşağı yönlü riski sınırlandırıyor.")
                    stance = Stance.BULLISH
                    confidence = 0.65
                    thesis = f"{data.symbol} için yükseliş risk parametreleri sıkı stop takibiyle yönetilebilir seviyede."
                    invalidation = data.current_price * 0.94
                elif tech.stance == sent.stance and "BEAR" in tech.stance.value:
                    risks.append("Haftalık bazda derinleşebilecek düzeltme riski; sermayeyi korumak birinci önceliktir.")
                    stance = Stance.STRONG_BEAR
                    confidence = 0.80
                    thesis = f"{data.symbol} üzerinde belirgin aşağı yönlü kırılganlık mevcut; long pozisyonlar risklidir."
                    invalidation = data.current_price * 1.05
                else:
                    risks.append("Teknik ve Duyarlılık arasında belirgin sinyal çelişkisi var. Testere piyasası riski yüksek.")
                    stance = Stance.NEUTRAL
                    confidence = 0.75
                    thesis = f"{data.symbol} için Risk/Kazanç oranı yönsüz bahis açmak için uygun değil. Nakit ve bekleme önerilir."
                    invalidation = data.current_price * 0.96
            else:
                stance = Stance.NEUTRAL
                confidence = 0.50
                thesis = "Ajanlar arası mutabakat henüz risk almak için yeterli değil."
                invalidation = data.current_price * 0.95
        else:
            # English
            risks.append(f"ATR Volatility is ${ind.atr_14:,.2f}; whipsaw moves can trigger tight stops.")
            if ind.rsi_14 > 65:
                risks.append("Late-cycle long crowdedness: risk of cascading liquidations.")
            elif ind.rsi_14 < 35:
                risks.append("Falling-knife dynamics: low liquidity support below current levels.")

            if tech and sent:
                if tech.stance == sent.stance and "BULL" in tech.stance.value:
                    key_points.append("Dual confirmation reduces asymmetric downside.")
                    stance = Stance.BULLISH
                    confidence = 0.65
                    thesis = f"Bullish risk parameters are manageable with strict stop discipline on {data.symbol}."
                    invalidation = data.current_price * 0.94
                elif tech.stance == sent.stance and "BEAR" in tech.stance.value:
                    risks.append("High probability of multi-week drawdown; preserve capital.")
                    stance = Stance.STRONG_BEAR
                    confidence = 0.80
                    thesis = f"Severe downside vulnerability on {data.symbol}."
                    invalidation = data.current_price * 1.05
                else:
                    risks.append("Signal conflict between Technicals and Sentiment. Whipsaw risk.")
                    stance = Stance.NEUTRAL
                    confidence = 0.75
                    thesis = f"Risk/Reward profile unacceptable on {data.symbol}. Capital preservation advised."
                    invalidation = data.current_price * 0.96
            else:
                stance = Stance.NEUTRAL
                confidence = 0.50
                thesis = "Insufficient cross-agent consensus."
                invalidation = data.current_price * 0.95

        return AgentThought(
            role=self.role,
            agent_name=self.get_name(lang),
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
        super().__init__(AgentRole.ARBITRATOR, "Sovereign AI", "Sovereign AI (Konsensüs Hakemi & Baş Stratejist)", "CHIEF-CONSENSUS")

    def synthesize(
        self, data: MarketData, round_thoughts: list[AgentThought], round_num: int, lang: str = "tr"
    ) -> tuple[Stance, int, float, str, str, str]:
        tech = next((t for t in round_thoughts if t.role == AgentRole.TECHNICAL), None)
        sent = next((t for t in round_thoughts if t.role == AgentRole.SENTIMENT), None)
        risk = next((t for t in round_thoughts if t.role == AgentRole.RISK), None)

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

        invalidation = risk.suggested_invalidation if (risk and risk.suggested_invalidation) else (data.current_price * 0.95)
        c_sym = data.currency

        if lang == "tr":
            stance_tr = STANCE_TR.get(final_stance, final_stance.value)
            thesis = (
                f"Konsensüs Swarm, {data.symbol} ({data.current_price:,.2f} {c_sym}) için %{conf} ağırlıklı güven skoruyla "
                f"'{stance_tr}' yönünde mutabakata vardı. "
                f"Teknik momentum değerlendirmesi ile Risk denetçisinin parametreleri uzlaştırıldı."
            )
            bull_case = tech.thesis if tech else "Teknik yükseliş trendi"
            bear_case = (risk.identified_risks[0] if risk and risk.identified_risks else "Aşağı yönlü volatilite riski")
        else:
            thesis = (
                f"Consensus Swarm settles on {final_stance.value} for {data.symbol} (${data.current_price:,.2f}) "
                f"with {conf}% weighted conviction. "
                f"Technical momentum meets Risk Assessment."
            )
            bull_case = tech.thesis if tech else "Technical trend momentum"
            bear_case = (risk.identified_risks[0] if risk and risk.identified_risks else "Macro drawdown risk")

        return final_stance, conf, invalidation, thesis, bull_case, bear_case
