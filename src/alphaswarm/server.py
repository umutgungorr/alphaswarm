"""Interactive Web Dashboard server for AlphaSwarm with Coin/Stock separation and TR/EN support."""

import http.server
import json
import socketserver
import urllib.parse
from alphaswarm.graph import AlphaSwarmGraph
from alphaswarm.market_data import COIN_CATALOGUE, STOCK_CATALOGUE, get_market_data, get_top_assets
from alphaswarm.models import Stance
from alphaswarm.reporters import generate_html_report, generate_markdown_report


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AlphaSwarm ⚡ Otonom Çoklu Ajan Piyasa İstihbarat & Konsensüs Paneli</title>
<style>
    :root {
        --bg-main: #090d16;
        --bg-card: #111827;
        --border-color: #1f2937;
        --text-primary: #f8fafc;
        --text-muted: #94a3b8;
        --cyan: #38bdf8;
        --green: #10b981;
        --red: #ef4444;
        --yellow: #eab308;
        --purple: #c084fc;
    }
    * { box-sizing: border-box; }
    body {
        background: var(--bg-main);
        color: var(--text-primary);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        margin: 0;
        padding: 0;
    }
    header {
        background: rgba(17, 24, 39, 0.90);
        backdrop-filter: blur(12px);
        border-bottom: 1px solid var(--border-color);
        padding: 16px 32px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        position: sticky;
        top: 0;
        z-index: 100;
    }
    .brand { display: flex; align-items: center; gap: 12px; }
    .brand-icon {
        background: linear-gradient(135deg, #0284c7, #38bdf8);
        width: 38px;
        height: 38px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
    }
    .brand-title { font-size: 20px; font-weight: 800; letter-spacing: -0.5px; }
    .lang-toggle {
        display: flex;
        background: #0f172a;
        border: 1px solid #334155;
        border-radius: 8px;
        overflow: hidden;
    }
    .lang-btn {
        background: transparent;
        border: none;
        color: var(--text-muted);
        padding: 6px 14px;
        font-size: 13px;
        font-weight: 700;
        cursor: pointer;
    }
    .lang-btn.active {
        background: var(--cyan);
        color: #090d16;
    }
    
    .container {
        max-width: 1200px;
        margin: 28px auto;
        padding: 0 24px;
    }

    /* Category Segment Tabs */
    .segment-tabs {
        display: flex;
        gap: 12px;
        margin-bottom: 20px;
    }
    .segment-tab {
        flex: 1;
        padding: 14px 20px;
        background: var(--bg-card);
        border: 2px solid var(--border-color);
        border-radius: 12px;
        color: var(--text-muted);
        font-size: 16px;
        font-weight: 800;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        transition: all 0.2s ease;
    }
    .segment-tab:hover { border-color: #38bdf866; color: #fff; }
    .segment-tab.active {
        background: rgba(56, 189, 248, 0.08);
        border-color: var(--cyan);
        color: var(--cyan);
        box-shadow: 0 0 20px -5px rgba(56, 189, 248, 0.3);
    }

    .control-panel {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 14px;
        padding: 24px;
        margin-bottom: 24px;
    }
    .input-group {
        display: flex;
        gap: 10px;
        margin-bottom: 16px;
        flex-wrap: wrap;
    }
    input[type="text"] {
        flex: 2;
        min-width: 220px;
        background: #0f172a;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 14px 18px;
        color: #fff;
        font-size: 16px;
        font-weight: 700;
        text-transform: uppercase;
        outline: none;
    }
    input[type="text"]:focus { border-color: var(--cyan); box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.25); }
    select {
        background: #0f172a;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 14px;
        color: #fff;
        font-size: 14px;
        font-weight: 600;
        outline: none;
    }
    button.btn-primary {
        background: linear-gradient(135deg, #0284c7, #0ea5e9);
        color: #fff;
        border: none;
        border-radius: 8px;
        padding: 14px 28px;
        font-size: 15px;
        font-weight: 800;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 8px;
        transition: transform 0.15s ease;
    }
    button.btn-primary:hover { opacity: 0.95; transform: translateY(-1px); }
    button.btn-primary:active { transform: translateY(0); }

    .quick-picks {
        display: flex;
        gap: 8px;
        align-items: center;
        flex-wrap: wrap;
    }
    .quick-pick-btn {
        background: #1e293b;
        border: 1px solid #334155;
        color: var(--text-muted);
        border-radius: 6px;
        padding: 6px 14px;
        font-size: 13px;
        font-weight: 700;
        cursor: pointer;
        transition: all 0.15s ease;
    }
    .quick-pick-btn:hover { color: #fff; border-color: var(--cyan); background: #334155; }

    /* Alert Banner */
    .error-banner {
        display: none;
        background: rgba(239, 68, 68, 0.15);
        border: 1px solid var(--red);
        color: #fca5a5;
        padding: 16px 20px;
        border-radius: 10px;
        margin-bottom: 24px;
        font-size: 14px;
        line-height: 1.5;
    }

    .grid-layout {
        display: grid;
        grid-template-columns: 360px 1fr;
        gap: 24px;
    }
    @media (max-width: 900px) { .grid-layout { grid-template-columns: 1fr; } }

    .card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 14px;
        padding: 24px;
        margin-bottom: 24px;
    }
    .card-title {
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: var(--text-muted);
        font-weight: 800;
        margin-bottom: 16px;
    }
    .stat-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0;
        border-bottom: 1px solid #1e293b;
        font-size: 14px;
    }
    .stat-row:last-child { border-bottom: none; }
    .stat-val { font-weight: 700; color: #fff; }

    .consensus-banner {
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
        border: 1px solid #334155;
        background: #1e293b;
    }
    .consensus-stance { font-size: 26px; font-weight: 900; margin-bottom: 8px; }
    .consensus-thesis { font-size: 15px; color: #cbd5e1; line-height: 1.6; }

    .debate-stream {
        display: flex;
        flex-direction: column;
        gap: 16px;
    }
    .agent-card {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 20px;
    }
    .agent-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 12px;
    }
    .agent-avatar { font-size: 26px; }
    .agent-name { font-weight: 800; font-size: 15px; }
    .agent-role { font-size: 12px; color: var(--text-muted); }
    .agent-badge {
        margin-left: auto;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 800;
    }
    .agent-thesis { font-size: 14px; color: #e2e8f0; line-height: 1.5; margin-bottom: 12px; font-style: italic; }
    .bullet-list { margin: 0; padding-left: 20px; font-size: 13px; color: #94a3b8; line-height: 1.6; }
    .bullet-risk { color: #f87171; }

    .loading-spinner {
        display: none;
        text-align: center;
        padding: 40px;
        color: var(--cyan);
        font-size: 18px;
        font-weight: 700;
    }
    .actions-bar {
        display: flex;
        gap: 12px;
        margin-top: 18px;
    }
</style>
</head>
<body>

<header>
    <div class="brand">
        <div class="brand-icon">⚡</div>
        <div>
            <div class="brand-title">ALPHASWARM</div>
            <div id="hdrSubtitle" style="color: var(--text-muted); font-size: 11px;">Otonom Çoklu Ajan Konsensüs Platformu</div>
        </div>
    </div>
    <div style="display: flex; gap: 14px; align-items: center;">
        <div class="lang-toggle">
            <button class="lang-btn active" id="btnLangTR" onclick="setLanguage('tr')">🇹🇷 TR</button>
            <button class="lang-btn" id="btnLangEN" onclick="setLanguage('en')">🇬🇧 EN</button>
        </div>
        <a href="https://github.com/umutgungorr/alphaswarm" target="_blank" style="color: var(--text-muted); font-size: 13px; text-decoration: none;">GitHub Repo ↗</a>
    </div>
</header>

<div class="container">
    <!-- Category Tabs: Kripto vs Hisse -->
    <div class="segment-tabs">
        <button class="segment-tab active" id="tabCrypto" onclick="switchCategory('CRYPTO')">
            <span style="font-size: 22px;">🪙</span>
            <div>
                <div id="lblTabCrypto">Kripto Paralar</div>
                <div style="font-size: 11px; color: var(--text-muted); font-weight: normal;">BTC, ETH, SOL, AVAX, BNB...</div>
            </div>
        </button>
        <button class="segment-tab" id="tabStock" onclick="switchCategory('EQUITY')">
            <span style="font-size: 22px;">📈</span>
            <div>
                <div id="lblTabStock">Hisse Senetleri & BIST</div>
                <div style="font-size: 11px; color: var(--text-muted); font-weight: normal;">NVDA, AAPL, TSLA, THYAO, ASELS...</div>
            </div>
        </button>
    </div>

    <!-- Error Alert Banner -->
    <div id="errorBanner" class="error-banner"></div>

    <div class="control-panel">
        <div class="input-group">
            <input type="text" id="symbolInput" value="BTC" placeholder="Sembol Girin (Örn: BTC, ETH)">
            <select id="roundsSelect">
                <option value="1">1 Münazara Turu (Hızlı)</option>
                <option value="2" selected>2 Münazara Turu (Derin Konsensüs)</option>
                <option value="3">3 Münazara Turu (Ultra Titiz)</option>
            </select>
            <button class="btn-primary" id="launchBtn" onclick="runAnalysis()">
                <span>🚀 Analizi Başlat</span>
            </button>
        </div>
        <div class="quick-picks" id="quickPills">
            <!-- Dynamically populated pills -->
        </div>
    </div>

    <div id="loading" class="loading-spinner">
        ⚡ Ajan Swarm'ı toplanıyor ve piyasa telemetrisi hesaplanıyor...
    </div>

    <div id="resultsArea">
        <div id="consensusBanner" class="consensus-banner">
            <div class="consensus-stance" id="verdictStance">KONSENSÜS BEKLENİYOR...</div>
            <div class="consensus-thesis" id="verdictThesis">Sembol seçip 'Analizi Başlat' butonuna tıklayın.</div>
            <div class="actions-bar" id="actionsBar" style="display: none;">
                <button class="quick-pick-btn" style="color: var(--cyan); border-color: var(--cyan);" onclick="downloadReport('html')">📥 HTML Raporu İndir</button>
                <button class="quick-pick-btn" onclick="downloadReport('md')">📄 Markdown Olarak Al</button>
            </div>
        </div>

        <div class="grid-layout">
            <div>
                <div class="card">
                    <div class="card-title" id="lblTelemetryTitle">Piyasa Telemetrisi & Göstergeler</div>
                    <div class="stat-row">
                        <span style="color: var(--text-muted);" id="lblPrice">Son Fiyat</span>
                        <span class="stat-val" id="statPrice">$0.00</span>
                    </div>
                    <div class="stat-row">
                        <span style="color: var(--text-muted);" id="lblChange">24 Saat Değişim</span>
                        <span class="stat-val" id="statChange">0.00%</span>
                    </div>
                    <div class="stat-row">
                        <span style="color: var(--text-muted);">RSI (14-Günlük)</span>
                        <span class="stat-val" id="statRSI">50.0</span>
                    </div>
                    <div class="stat-row">
                        <span style="color: var(--text-muted);">50 / 200 SMA Trend</span>
                        <span class="stat-val" id="statSMA">NÖTR</span>
                    </div>
                    <div class="stat-row">
                        <span style="color: var(--text-muted);">Bollinger Bantları</span>
                        <span class="stat-val" id="statBB">$0 - $0</span>
                    </div>
                    <div class="stat-row">
                        <span style="color: var(--text-muted);" id="lblInval">Stop Invalidation</span>
                        <span class="stat-val" id="statInval" style="color: var(--red);">$0.00</span>
                    </div>
                </div>

                <div class="card">
                    <div class="card-title" id="lblSwarmRosterTitle">Swarm Ajan Heyeti</div>
                    <div style="font-size: 13px; line-height: 1.8; color: var(--text-muted);">
                        <div>📐 <strong>Aria Vance</strong> &bull; <span id="rRole1">Quant / Momentum Analisti</span></div>
                        <div>📰 <strong>Marcus Cole</strong> &bull; <span id="rRole2">Makro & Haber Duyarlılığı</span></div>
                        <div>🛡️ <strong>Vesper Sterling</strong> &bull; <span id="rRole3">Şeytanın Avukatı / Risk</span></div>
                        <div>⚖️ <strong>Sovereign AI</strong> &bull; <span id="rRole4">Konsensüs Hakemi</span></div>
                    </div>
                </div>
            </div>

            <div>
                <div class="card">
                    <div class="card-title" id="lblArenaTitle">Canlı Ajan Münazara Arenası</div>
                    <div class="debate-stream" id="debateStream">
                        <!-- Agent bubbles injected here -->
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
let currentCategory = "CRYPTO";
let currentLang = "tr";
let currentSymbol = "BTC";

const COIN_PILLS = ["BTC", "ETH", "SOL", "AVAX", "BNB", "XRP", "LINK", "SUI", "PEPE", "NEAR"];
const STOCK_PILLS = ["NVDA", "AAPL", "MSFT", "TSLA", "AMZN", "AMD", "SPY", "THYAO", "ASELS", "EREGL"];

const I18N = {
    tr: {
        subtitle: "Otonom Çoklu Ajan Konsensüs Platformu",
        tabCrypto: "Kripto Paralar",
        tabStock: "Hisse Senetleri & BIST",
        placeholderCrypto: "Coin Sembolü (Örn: BTC, ETH, SOL, AVAX)",
        placeholderStock: "Hisse Sembolü (Örn: NVDA, AAPL, THYAO, TSLA)",
        btnLaunch: "🚀 Analizi Başlat",
        telemetry: "Piyasa Telemetrisi & Göstergeler",
        price: "Son Fiyat",
        change: "24 Saat Değişim",
        inval: "Stop Invalidation",
        roster: "Swarm Ajan Heyeti",
        rRole1: "Quant / Momentum Analisti",
        rRole2: "Makro & Haber Duyarlılığı",
        rRole3: "Şeytanın Avukatı / Risk Yöneticisi",
        rRole4: "Konsensüs Hakemi",
        arena: "Canlı Ajan Münazara Arenası",
        roundOpt1: "1 Münazara Turu (Hızlı)",
        roundOpt2: "2 Münazara Turu (Derin Konsensüs)",
        roundOpt3: "3 Münazara Turu (Ultra Titiz)",
        downloadHtml: "📥 HTML Raporu İndir",
        downloadMd: "📄 Markdown Olarak Al",
        loadingMsg: "⚡ Ajan Swarm'ı toplanıyor ve piyasa telemetrisi hesaplanıyor...",
        waitingThesis: "Sembol seçip 'Analizi Başlat' butonuna tıklayın."
    },
    en: {
        subtitle: "Autonomous Multi-Agent Consensus Platform",
        tabCrypto: "Cryptocurrencies",
        tabStock: "Equities & Stocks",
        placeholderCrypto: "Coin Symbol (e.g. BTC, ETH, SOL, AVAX)",
        placeholderStock: "Stock Symbol (e.g. NVDA, AAPL, TSLA, SPY)",
        btnLaunch: "🚀 Launch Swarm",
        telemetry: "Market Telemetry & Technicals",
        price: "Last Price",
        change: "24h Change",
        inval: "Stop Invalidation",
        roster: "Swarm Roster",
        rRole1: "Quant / Technical Lead",
        rRole2: "Macro & Sentiment Lead",
        rRole3: "Devil's Advocate / Risk",
        rRole4: "Consensus Arbitrator",
        arena: "Live Multi-Agent Debate Arena",
        roundOpt1: "1 Debate Round (Fast)",
        roundOpt2: "2 Debate Rounds (Deep)",
        roundOpt3: "3 Debate Rounds (Ultra)",
        downloadHtml: "📥 Download HTML Dossier",
        downloadMd: "📄 Download Markdown",
        loadingMsg: "⚡ Mobilizing agent swarm and computing market telemetry...",
        waitingThesis: "Select a ticker and click 'Launch Swarm' to begin."
    }
};

function setLanguage(lang) {
    currentLang = lang;
    document.getElementById("btnLangTR").className = "lang-btn" + (lang === "tr" ? " active" : "");
    document.getElementById("btnLangEN").className = "lang-btn" + (lang === "en" ? " active" : "");

    const t = I18N[lang];
    document.getElementById("hdrSubtitle").textContent = t.subtitle;
    document.getElementById("lblTabCrypto").textContent = t.tabCrypto;
    document.getElementById("lblTabStock").textContent = t.tabStock;
    document.getElementById("launchBtn").innerHTML = `<span>${t.btnLaunch}</span>`;
    document.getElementById("lblTelemetryTitle").textContent = t.telemetry;
    document.getElementById("lblPrice").textContent = t.price;
    document.getElementById("lblChange").textContent = t.change;
    document.getElementById("lblInval").textContent = t.inval;
    document.getElementById("lblSwarmRosterTitle").textContent = t.roster;
    document.getElementById("rRole1").textContent = t.rRole1;
    document.getElementById("rRole2").textContent = t.rRole2;
    document.getElementById("rRole3").textContent = t.rRole3;
    document.getElementById("rRole4").textContent = t.rRole4;
    document.getElementById("lblArenaTitle").textContent = t.arena;
    document.getElementById("loading").textContent = t.loadingMsg;

    const sel = document.getElementById("roundsSelect");
    sel.options[0].text = t.roundOpt1;
    sel.options[1].text = t.roundOpt2;
    sel.options[2].text = t.roundOpt3;

    updatePlaceholder();
    runAnalysis();
}

function switchCategory(cat) {
    currentCategory = cat;
    document.getElementById("tabCrypto").className = "segment-tab" + (cat === "CRYPTO" ? " active" : "");
    document.getElementById("tabStock").className = "segment-tab" + (cat === "EQUITY" ? " active" : "");
    
    updatePlaceholder();
    renderQuickPills();

    const defaultSym = cat === "CRYPTO" ? "BTC" : "NVDA";
    document.getElementById("symbolInput").value = defaultSym;
    runAnalysis();
}

function updatePlaceholder() {
    const t = I18N[currentLang];
    document.getElementById("symbolInput").placeholder = currentCategory === "CRYPTO" ? t.placeholderCrypto : t.placeholderStock;
}

function renderQuickPills() {
    const container = document.getElementById("quickPills");
    container.innerHTML = `<span style="font-size: 12px; color: var(--text-muted);">${currentLang === 'tr' ? 'Hızlı Seçim:' : 'Quick Pick:'}</span>`;
    const pills = currentCategory === "CRYPTO" ? COIN_PILLS : STOCK_PILLS;
    pills.forEach(sym => {
        const btn = document.createElement("button");
        btn.className = "quick-pick-btn";
        btn.textContent = sym;
        btn.onclick = () => {
            document.getElementById("symbolInput").value = sym;
            runAnalysis();
        };
        container.appendChild(btn);
    });
}

async function runAnalysis() {
    const symInput = document.getElementById("symbolInput").value.trim().toUpperCase();
    if (!symInput) return;

    currentSymbol = symInput;
    const rounds = document.getElementById("roundsSelect").value;
    const errBanner = document.getElementById("errorBanner");
    errBanner.style.display = "none";

    document.getElementById("loading").style.display = "block";
    document.getElementById("resultsArea").style.opacity = "0.3";

    try {
        const url = `/api/analyze?symbol=${encodeURIComponent(symInput)}&asset_type=${currentCategory}&rounds=${rounds}&lang=${currentLang}`;
        const resp = await fetch(url);
        const data = await resp.json();

        if (!resp.ok) {
            errBanner.textContent = data.error || "Geçersiz sembol!";
            errBanner.style.display = "block";
            return;
        }

        renderResults(data);
    } catch (err) {
        errBanner.textContent = "Bağlantı hatası: " + err;
        errBanner.style.display = "block";
    } finally {
        document.getElementById("loading").style.display = "none";
        document.getElementById("resultsArea").style.opacity = "1.0";
    }
}

function renderResults(data) {
    const v = data.verdict;
    const m = data.market_data;
    const ind = m.indicators;

    const isBull = v.final_stance.includes("BULL");
    const isBear = v.final_stance.includes("BEAR");
    const color = isBull ? "var(--green)" : (isBear ? "var(--red)" : "var(--yellow)");

    const banner = document.getElementById("consensusBanner");
    banner.style.borderLeft = `6px solid ${color}`;
    
    // TR Stance translation
    let displayStance = v.final_stance;
    if (currentLang === "tr") {
        if (v.final_stance === "STRONG_BULL") displayStance = "GÜÇLÜ YÜKSELİŞ (STRONG BULL)";
        else if (v.final_stance === "BULLISH") displayStance = "YÜKSELİŞ (BULLISH)";
        else if (v.final_stance === "NEUTRAL") displayStance = "NÖTR / BEKLE (NEUTRAL)";
        else if (v.final_stance === "BEARISH") displayStance = "DÜŞÜŞ (BEARISH)";
        else if (v.final_stance === "STRONG_BEAR") displayStance = "GÜÇLÜ DÜŞÜŞ (STRONG BEAR)";
    }

    document.getElementById("verdictStance").textContent = `${displayStance} (%${v.confidence_score} Güven)`;
    document.getElementById("verdictStance").style.color = color;
    document.getElementById("verdictThesis").textContent = v.primary_thesis;
    document.getElementById("actionsBar").style.display = "flex";

    // Stats
    const curSymbol = m.currency === "TRY" ? "₺" : "$";
    document.getElementById("statPrice").textContent = `${curSymbol}${m.current_price.toLocaleString(undefined, {minimumFractionDigits: 2})}`;
    const chgEl = document.getElementById("statChange");
    chgEl.textContent = `${m.change_24h_pct >= 0 ? '+' : ''}${m.change_24h_pct.toFixed(2)}%`;
    chgEl.style.color = m.change_24h_pct >= 0 ? "var(--green)" : "var(--red)";
    
    document.getElementById("statRSI").textContent = ind.rsi_14.toFixed(1);
    document.getElementById("statSMA").textContent = ind.trend_50_200;
    document.getElementById("statBB").textContent = `${curSymbol}${ind.bollinger_lower.toLocaleString()} - ${curSymbol}${ind.bollinger_upper.toLocaleString()}`;
    document.getElementById("statInval").textContent = `${curSymbol}${v.key_invalidation_level.toLocaleString(undefined, {minimumFractionDigits: 2})}`;

    // Debate Arena
    const stream = document.getElementById("debateStream");
    stream.innerHTML = "";

    v.debate_rounds.forEach(r => {
        const roundTitle = document.createElement("div");
        roundTitle.style.cssText = "font-size: 12px; color: var(--cyan); text-transform: uppercase; letter-spacing: 1px; font-weight: 800; margin: 12px 0 6px 0;";
        roundTitle.textContent = currentLang === 'tr' 
            ? `▶ Münazara Turu #${r.round_number} (${r.consensus_shift_notes})` 
            : `▶ Debate Round #${r.round_number} (${r.consensus_shift_notes})`;
        stream.appendChild(roundTitle);

        r.thoughts.forEach(t => {
            const isTBull = t.stance.includes("BULL");
            const isTBear = t.stance.includes("BEAR");
            const tColor = isTBull ? "var(--green)" : (isTBear ? "var(--red)" : "var(--yellow)");
            const icon = t.role === "TECHNICAL" ? "📐" : (t.role === "SENTIMENT" ? "📰" : "🛡️");

            const card = document.createElement("div");
            card.className = "agent-card";
            card.innerHTML = `
                <div class="agent-header">
                    <span class="agent-avatar">${icon}</span>
                    <div>
                        <div class="agent-name">${t.agent_name}</div>
                        <div class="agent-role">[${t.callsign}] &bull; ${t.role}</div>
                    </div>
                    <span class="agent-badge" style="background: ${tColor}22; color: ${tColor}; border: 1px solid ${tColor}66;">
                        ${t.stance} (%${Math.round(t.confidence * 100)})
                    </span>
                </div>
                <div class="agent-thesis">"${t.thesis}"</div>
                <ul class="bullet-list">
                    ${t.key_points.map(p => `<li>${p}</li>`).join("")}
                    ${t.identified_risks.map(rk => `<li class="bullet-risk">⚠️ ${rk}</li>`).join("")}
                </ul>
            `;
            stream.appendChild(card);
        });
    });
}

function downloadReport(fmt) {
    window.open(`/api/report/${fmt}?symbol=${encodeURIComponent(currentSymbol)}&asset_type=${currentCategory}&lang=${currentLang}`, '_blank');
}

window.addEventListener("DOMContentLoaded", () => {
    renderQuickPills();
    runAnalysis();
});
</script>

</body>
</html>
"""


class AlphaSwarmHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)

        if parsed.path == "/" or parsed.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode("utf-8"))
            return

        elif parsed.path == "/api/analyze":
            symbol = qs.get("symbol", ["BTC"])[0].upper().strip()
            asset_type = qs.get("asset_type", [None])[0]
            rounds = int(qs.get("rounds", [2])[0])
            lang = qs.get("lang", ["tr"])[0].lower()

            try:
                market_data = get_market_data(symbol, asset_type=asset_type)
            except ValueError as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}, ensure_ascii=False).encode("utf-8"))
                return

            graph = AlphaSwarmGraph(max_rounds=rounds)
            verdict = graph.propagate(market_data, lang=lang)

            res = {
                "market_data": market_data.to_dict(),
                "verdict": verdict.to_dict(),
            }
            body = json.dumps(res, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
            return

        elif parsed.path.startswith("/api/report/"):
            fmt = parsed.path.split("/")[-1]
            symbol = qs.get("symbol", ["BTC"])[0].upper().strip()
            asset_type = qs.get("asset_type", [None])[0]
            lang = qs.get("lang", ["tr"])[0].lower()

            try:
                market_data = get_market_data(symbol, asset_type=asset_type)
            except ValueError as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(str(e).encode("utf-8"))
                return

            graph = AlphaSwarmGraph(max_rounds=2)
            verdict = graph.propagate(market_data, lang=lang)

            if fmt == "html":
                content = generate_html_report(verdict, market_data)
                mime = "text/html; charset=utf-8"
            else:
                content = generate_markdown_report(verdict, market_data)
                mime = "text/markdown; charset=utf-8"

            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"Not Found")

    def log_message(self, format, *args):
        return


def start_server(port: int = 5050):
    server_address = ("", port)
    with socketserver.TCPServer(server_address, AlphaSwarmHandler) as httpd:
        print(f"\033[1m\033[36m⚡ AlphaSwarm Interactive Dashboard is live at:\033[0m")
        print(f"   \033[32mhttp://localhost:{port}\033[0m (or http://127.0.0.1:{port})")
        print("   Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down AlphaSwarm server.")
