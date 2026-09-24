"""Interactive High-Performance Web Dashboard server for AlphaSwarm."""

import http.server
import json
import socketserver
import urllib.parse
from alphaswarm.graph import AlphaSwarmGraph
from alphaswarm.market_data import (
    COIN_CATALOGUE,
    STOCK_CATALOGUE,
    get_market_data,
    get_top_assets,
)
from alphaswarm.models import Stance
from alphaswarm.reporters import generate_html_report, generate_markdown_report


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AlphaSwarm ⚡ Otonom Çoklu Ajan Piyasa İstihbarat & Konsensüs Hub</title>
<style>
    :root {
        --bg-main: #070b12;
        --bg-card: #0f172a;
        --bg-card-sub: #1e293b;
        --border-color: #1e293b;
        --border-highlight: #334155;
        --text-primary: #f8fafc;
        --text-muted: #94a3b8;
        --cyan: #38bdf8;
        --green: #10b981;
        --red: #ef4444;
        --yellow: #f59e0b;
        --purple: #a855f7;
    }
    * { box-sizing: border-box; }
    body {
        background: var(--bg-main);
        color: var(--text-primary);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        margin: 0;
        padding: 0;
        overflow-x: hidden;
    }
    header {
        background: rgba(15, 23, 42, 0.92);
        backdrop-filter: blur(14px);
        border-bottom: 1px solid var(--border-color);
        padding: 14px 28px;
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
        border-radius: 9px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.3);
    }
    .brand-title { font-size: 20px; font-weight: 900; letter-spacing: -0.5px; }
    
    .lang-toggle {
        display: flex;
        background: #090d16;
        border: 1px solid var(--border-highlight);
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
        transition: all 0.2s;
    }
    .lang-btn.active { background: var(--cyan); color: #090d16; }

    .container {
        max-width: 1280px;
        margin: 24px auto;
        padding: 0 20px;
    }

    /* Category Switcher Tabs */
    .segment-tabs {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        margin-bottom: 18px;
    }
    .segment-tab {
        padding: 14px 20px;
        background: var(--bg-card);
        border: 2px solid var(--border-color);
        border-radius: 12px;
        color: var(--text-muted);
        font-size: 15px;
        font-weight: 800;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 12px;
        transition: all 0.2s ease;
    }
    .segment-tab:hover { border-color: #38bdf855; color: #fff; }
    .segment-tab.active {
        background: rgba(56, 189, 248, 0.08);
        border-color: var(--cyan);
        color: var(--cyan);
        box-shadow: 0 0 20px -5px rgba(56, 189, 248, 0.25);
    }

    /* Control Box */
    .control-box {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .input-bar {
        display: flex;
        gap: 10px;
        margin-bottom: 14px;
        flex-wrap: wrap;
    }
    input[type="text"] {
        flex: 2;
        min-width: 220px;
        background: #070b12;
        border: 1px solid var(--border-highlight);
        border-radius: 8px;
        padding: 12px 18px;
        color: #fff;
        font-size: 16px;
        font-weight: 800;
        text-transform: uppercase;
        outline: none;
    }
    input[type="text"]:focus { border-color: var(--cyan); box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.25); }
    select {
        background: #070b12;
        border: 1px solid var(--border-highlight);
        border-radius: 8px;
        padding: 12px 16px;
        color: #fff;
        font-size: 14px;
        font-weight: 600;
        outline: none;
    }
    button.btn-launch {
        background: linear-gradient(135deg, #0284c7, #0ea5e9);
        color: #fff;
        border: none;
        border-radius: 8px;
        padding: 12px 28px;
        font-size: 15px;
        font-weight: 800;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 8px;
        transition: transform 0.15s ease;
    }
    button.btn-launch:hover { opacity: 0.95; transform: translateY(-1px); }
    button.btn-launch:active { transform: translateY(0); }

    .pills-container {
        display: flex;
        gap: 8px;
        align-items: center;
        flex-wrap: wrap;
    }
    .pill {
        background: #1e293b;
        border: 1px solid #334155;
        color: var(--text-muted);
        border-radius: 6px;
        padding: 5px 12px;
        font-size: 12px;
        font-weight: 700;
        cursor: pointer;
        transition: all 0.15s;
    }
    .pill:hover { color: #fff; border-color: var(--cyan); background: #334155; }
    .pill.active { background: var(--cyan); color: #090d16; border-color: var(--cyan); }

    /* Alert Banner */
    .error-alert {
        display: none;
        background: rgba(239, 68, 68, 0.15);
        border: 1px solid var(--red);
        color: #fca5a5;
        padding: 14px 18px;
        border-radius: 10px;
        margin-bottom: 20px;
        font-size: 14px;
        font-weight: 600;
    }

    /* Consensus Hero Card */
    .consensus-hero {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-left: 6px solid var(--cyan);
        border-radius: 14px;
        padding: 24px;
        margin-bottom: 24px;
        transition: border-color 0.3s;
    }
    .hero-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
        margin-bottom: 12px;
    }
    .hero-stance { font-size: 24px; font-weight: 900; }
    .hero-thesis { font-size: 15px; color: #cbd5e1; line-height: 1.6; }

    /* Main Grid: Chart + Debates */
    .dashboard-grid {
        display: grid;
        grid-template-columns: 1fr 480px;
        gap: 20px;
        margin-bottom: 28px;
    }
    @media (max-width: 1080px) {
        .dashboard-grid { grid-template-columns: 1fr; }
    }

    .card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 14px;
        padding: 20px;
    }
    .card-hdr {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
    }
    .card-title {
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: var(--text-muted);
        font-weight: 800;
    }

    /* Canvas Chart Container */
    .chart-container {
        position: relative;
        width: 100%;
        height: 380px;
        background: #070b12;
        border: 1px solid #1e293b;
        border-radius: 10px;
        overflow: hidden;
    }
    canvas {
        display: block;
        width: 100%;
        height: 100%;
    }
    .chart-legend {
        display: flex;
        gap: 16px;
        font-size: 11px;
        font-weight: 700;
        margin-top: 10px;
        flex-wrap: wrap;
    }
    .legend-item { display: flex; align-items: center; gap: 6px; }
    .legend-color { width: 12px; height: 3px; border-radius: 2px; }

    /* Telemetry Gauges */
    .gauges-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
        gap: 12px;
        margin-top: 18px;
    }
    .gauge-card {
        background: #070b12;
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 12px;
        text-align: center;
    }
    .gauge-val { font-size: 18px; font-weight: 900; color: #fff; margin: 4px 0; }
    .gauge-lbl { font-size: 10px; text-transform: uppercase; color: var(--text-muted); font-weight: 700; }

    /* Progress bar gauge */
    .gauge-bar-wrap {
        height: 6px;
        background: #1e293b;
        border-radius: 3px;
        margin-top: 6px;
        overflow: hidden;
    }
    .gauge-bar-fill {
        height: 100%;
        border-radius: 3px;
        transition: width 0.4s ease;
    }

    /* Live Debate Arena */
    .debate-arena {
        display: flex;
        flex-direction: column;
        gap: 14px;
        max-height: 680px;
        overflow-y: auto;
        padding-right: 4px;
    }
    .agent-card {
        background: #070b12;
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 16px;
        transition: transform 0.2s, border-color 0.2s;
        animation: fadeIn 0.3s ease forwards;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(6px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .agent-top {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 10px;
    }
    .agent-avatar { font-size: 24px; }
    .agent-name { font-weight: 800; font-size: 14px; }
    .agent-callsign { font-size: 11px; color: var(--text-muted); font-weight: 700; }
    .agent-badge {
        margin-left: auto;
        padding: 3px 8px;
        border-radius: 5px;
        font-size: 11px;
        font-weight: 800;
    }
    .agent-speech { font-size: 13px; color: #cbd5e1; line-height: 1.5; font-style: italic; margin-bottom: 10px; }
    .agent-ul { margin: 0; padding-left: 18px; font-size: 12px; color: var(--text-muted); line-height: 1.5; }
    .risk-li { color: #f87171; }

    /* Stepping status ticker */
    .swarm-status-bar {
        background: rgba(56, 189, 248, 0.08);
        border: 1px dashed var(--cyan);
        color: var(--cyan);
        padding: 10px 16px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 700;
        display: none;
        align-items: center;
        gap: 10px;
        margin-bottom: 16px;
    }

    /* Market Radar Table */
    .radar-table-wrap {
        overflow-x: auto;
    }
    table.radar-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        text-align: left;
    }
    table.radar-table th {
        background: #070b12;
        color: var(--text-muted);
        padding: 10px 14px;
        border-bottom: 1px solid var(--border-color);
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    table.radar-table td {
        padding: 12px 14px;
        border-bottom: 1px solid #1e293b;
        color: #f1f5f9;
    }
    table.radar-table tr:hover td {
        background: rgba(56, 189, 248, 0.04);
        cursor: pointer;
    }
</style>
</head>
<body>

<header>
    <div class="brand">
        <div class="brand-icon">⚡</div>
        <div>
            <div class="brand-title">ALPHASWARM</div>
            <div id="hdrSubtitle" style="color: var(--text-muted); font-size: 11px;">Otonom Çoklu Ajan Konsensüs & Piyasa İstihbarat Platformu</div>
        </div>
    </div>
    <div style="display: flex; gap: 14px; align-items: center;">
        <div class="lang-toggle">
            <button class="lang-btn active" id="btnLangTR" onclick="setLanguage('tr')">🇹🇷 TR</button>
            <button class="lang-btn" id="btnLangEN" onclick="setLanguage('en')">🇬🇧 EN</button>
        </div>
        <a href="https://github.com/umutgungorr/alphaswarm" target="_blank" style="color: var(--text-muted); font-size: 13px; text-decoration: none; font-weight: 600;">GitHub Repo ↗</a>
    </div>
</header>

<div class="container">
    <!-- Category Tabs -->
    <div class="segment-tabs">
        <button class="segment-tab active" id="tabCrypto" onclick="switchCategory('CRYPTO')">
            <span style="font-size: 24px;">🪙</span>
            <div>
                <div id="lblTabCrypto">Kripto Varlıklar (Coins)</div>
                <div style="font-size: 11px; color: var(--text-muted); font-weight: normal;">BTC, ETH, SOL, AVAX, BNB, XRP, SUI, LINK...</div>
            </div>
        </button>
        <button class="segment-tab" id="tabStock" onclick="switchCategory('EQUITY')">
            <span style="font-size: 24px;">📈</span>
            <div>
                <div id="lblTabStock">Hisse Senetleri & BIST (Stocks)</div>
                <div style="font-size: 11px; color: var(--text-muted); font-weight: normal;">NVDA, AAPL, MSFT, TSLA, THYAO, ASELS, SPY...</div>
            </div>
        </button>
    </div>

    <!-- Error Alert Box -->
    <div id="errorAlert" class="error-alert"></div>

    <!-- Control Box -->
    <div class="control-box">
        <div class="input-bar">
            <input type="text" id="symbolInput" value="BTC" placeholder="Sembol (BTC, ETH, NVDA, THYAO)">
            <select id="roundsSelect">
                <option value="1">1 Münazara Turu (Hızlı)</option>
                <option value="2" selected>2 Münazara Turu (Derin)</option>
                <option value="3">3 Münazara Turu (Ultra)</option>
            </select>
            <button class="btn-launch" id="launchBtn" onclick="runAnalysis()">
                <span>🚀 Analizi Başlat</span>
            </button>
        </div>
        <div class="pills-container" id="pillsContainer"></div>
    </div>

    <!-- Live Agent Thinking Status Bar -->
    <div id="swarmStatusBar" class="swarm-status-bar">
        <span class="spinner" style="font-size: 18px;">⏳</span>
        <span id="swarmStatusMsg">Ajan Swarm'ı toplanıyor...</span>
    </div>

    <!-- Consensus Hero Card -->
    <div id="consensusHero" class="consensus-hero">
        <div class="hero-top">
            <div class="hero-stance" id="verdictStance">KONSENSÜS BEKLENİYOR...</div>
            <div style="display: flex; gap: 8px;">
                <button class="pill" style="color: var(--cyan); border-color: var(--cyan);" onclick="downloadReport('html')">📥 HTML Rapor</button>
                <button class="pill" onclick="downloadReport('md')">📄 Markdown</button>
            </div>
        </div>
        <div class="hero-thesis" id="verdictThesis">Analiz başlatmak için yukarıdaki 'Analizi Başlat' butonuna tıklayın.</div>
    </div>

    <!-- Main Dashboard Grid -->
    <div class="dashboard-grid">
        <!-- Left: Real Price Action Chart & Telemetry -->
        <div>
            <div class="card" style="margin-bottom: 20px;">
                <div class="card-hdr">
                    <div>
                        <span class="card-title" id="lblChartTitle">Canlı Fiyat Grafiği & Teknik Bantlar</span>
                        <div id="chartAssetHeader" style="font-size: 18px; font-weight: 900; color: #fff; margin-top: 4px;">BTC / USD</div>
                    </div>
                    <div style="text-align: right;">
                        <div id="chartPrice" style="font-size: 20px; font-weight: 800; color: var(--cyan);">$0.00</div>
                        <div id="chartChange" style="font-size: 12px; font-weight: 700;">+0.00%</div>
                    </div>
                </div>

                <div class="chart-container">
                    <canvas id="candleCanvas"></canvas>
                </div>

                <div class="chart-legend">
                    <div class="legend-item"><div class="legend-color" style="background: #10b981;"></div><span id="lblLgBull">Boğa Mumu</span></div>
                    <div class="legend-item"><div class="legend-color" style="background: #ef4444;"></div><span id="lblLgBear">Ayı Mumu</span></div>
                    <div class="legend-item"><div class="legend-color" style="background: #38bdf8;"></div><span>SMA 50</span></div>
                    <div class="legend-item"><div class="legend-color" style="background: #a855f7;"></div><span>SMA 200</span></div>
                    <div class="legend-item"><div class="legend-color" style="background: #f87171; border-top: 1px dashed #f87171;"></div><span id="lblLgStop">Stop Invalidation</span></div>
                </div>

                <!-- Gauges -->
                <div class="gauges-grid">
                    <div class="gauge-card">
                        <div class="gauge-lbl">RSI (14-GÜN)</div>
                        <div class="gauge-val" id="valRSI">50.0</div>
                        <div class="gauge-bar-wrap">
                            <div class="gauge-bar-fill" id="barRSI" style="width: 50%; background: var(--cyan);"></div>
                        </div>
                    </div>
                    <div class="gauge-card">
                        <div class="gauge-lbl" id="lblFgTitle">KORKU & AÇGÖZLÜLÜK</div>
                        <div class="gauge-val" id="valFG">50</div>
                        <div class="gauge-bar-wrap">
                            <div class="gauge-bar-fill" id="barFG" style="width: 50%; background: var(--yellow);"></div>
                        </div>
                    </div>
                    <div class="gauge-card">
                        <div class="gauge-lbl">50/200 TREND</div>
                        <div class="gauge-val" id="valSMA" style="font-size: 13px;">NÖTR</div>
                    </div>
                    <div class="gauge-card">
                        <div class="gauge-lbl" id="lblStopTitle">STOP İPTAL</div>
                        <div class="gauge-val" id="valInval" style="color: var(--red);">$0.00</div>
                    </div>
                </div>
            </div>

            <!-- Screener Radar Table -->
            <div class="card">
                <div class="card-title" id="lblRadarTitle">⚡ Çoklu Varlık Radarı & Hızlı Tarama</div>
                <div class="radar-table-wrap">
                    <table class="radar-table">
                        <thead>
                            <tr>
                                <th>Sembol</th>
                                <th>Varlık Adı</th>
                                <th>Son Fiyat</th>
                                <th>24h %</th>
                                <th>RSI</th>
                                <th>İşlem</th>
                            </tr>
                        </thead>
                        <tbody id="radarTbody">
                            <!-- Injected rows -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Right: Live Debate Arena -->
        <div class="card">
            <div class="card-hdr">
                <span class="card-title" id="lblArenaTitle">Canlı Ajan Münazara Arenası</span>
                <span style="font-size: 11px; color: var(--cyan); font-weight: 700;">4 OTONOM AJAN</span>
            </div>
            <div class="debate-arena" id="debateArena">
                <!-- Live Agent Bubbles streamed here -->
            </div>
        </div>
    </div>
</div>

<script>
let currentCategory = "CRYPTO";
let currentLang = "tr";
let currentSymbol = "BTC";
let currentCandles = [];
let currentVerdict = null;

const COIN_LIST = [
    { s: "BTC", n: "Bitcoin", p: 64500, c: 2.45, r: 61.2 },
    { s: "ETH", n: "Ethereum", p: 3450, c: -1.15, r: 48.5 },
    { s: "SOL", n: "Solana", p: 148, c: 4.80, r: 66.4 },
    { s: "AVAX", n: "Avalanche", p: 28.5, c: 3.20, r: 58.1 },
    { s: "BNB", n: "BNB", p: 585, c: 0.90, r: 52.0 },
    { s: "XRP", n: "XRP", p: 0.58, c: -0.40, r: 47.0 },
    { s: "SUI", n: "Sui", p: 1.65, c: 7.40, r: 69.5 },
    { s: "LINK", n: "Chainlink", p: 11.8, c: 1.80, r: 54.0 },
];

const STOCK_LIST = [
    { s: "NVDA", n: "NVIDIA Corp.", p: 225.5, c: 2.10, r: 63.5 },
    { s: "AAPL", n: "Apple Inc.", p: 337.0, c: 0.85, r: 58.0 },
    { s: "MSFT", n: "Microsoft Corp.", p: 430.0, c: -0.60, r: 49.2 },
    { s: "TSLA", n: "Tesla Inc.", p: 380.1, c: 3.80, r: 65.0 },
    { s: "THYAO", n: "Türk Hava Yolları", p: 298.5, c: 1.75, r: 56.4 },
    { s: "ASELS", n: "Aselsan", p: 62.5, c: 0.80, r: 53.0 },
    { s: "EREGL", n: "Ereğli Demir Çelik", p: 52.0, c: -1.10, r: 46.0 },
    { s: "SPY", n: "S&P 500 ETF", p: 560.0, c: 0.45, r: 54.0 },
];

const I18N = {
    tr: {
        subtitle: "Otonom Çoklu Ajan Konsensüs & Piyasa İstihbarat Platformu",
        tabCrypto: "Kripto Varlıklar (Coins)",
        tabStock: "Hisse Senetleri & BIST (Stocks)",
        btnLaunch: "🚀 Analizi Başlat",
        chartTitle: "Canlı Fiyat Grafiği & Teknik Bantlar",
        radarTitle: "⚡ Çoklu Varlık Radarı & Hızlı Tarama",
        arenaTitle: "Canlı Ajan Münazara Arenası",
        lgBull: "Boğa Mumu",
        lgBear: "Ayı Mumu",
        lgStop: "Stop İptal Seviyesi",
        lblFg: "KORKU & AÇGÖZLÜLÜK",
        lblStop: "STOP İPTAL",
        waitingThesis: "Analiz başlatmak için yukarıdaki 'Analizi Başlat' butonuna tıklayın.",
        steps: [
            "Aria Vance (Quant) mum grafiklerini ve RSI/SMA/MACD göstergelerini hesaplıyor...",
            "Marcus Cole (Makro/Haber) kurumsal fon akışlarını ve duyarlılığı değerlendiriyor...",
            "Vesper Sterling (Risk) tersine riskleri ve stop patlatma tuzaklarını inceliyor...",
            "Sovereign AI (Konsensüs) tüm argümanları tartıp nihai kararı oluşturuyor..."
        ]
    },
    en: {
        subtitle: "Autonomous Multi-Agent Consensus & Market Intelligence Platform",
        tabCrypto: "Cryptocurrencies (Coins)",
        tabStock: "Equities & Stocks",
        btnLaunch: "🚀 Launch Swarm",
        chartTitle: "Live Price Action & Technical Bands",
        radarTitle: "⚡ Multi-Asset Radar & Screener",
        arenaTitle: "Live Multi-Agent Debate Arena",
        lgBull: "Bull Candle",
        lgBear: "Bear Candle",
        lgStop: "Stop Invalidation Level",
        lblFg: "FEAR & GREED",
        lblStop: "STOP INVALIDATION",
        waitingThesis: "Click 'Launch Swarm' to begin multi-agent consensus analysis.",
        steps: [
            "Aria Vance (Quant Lead) computing candle indicators & momentum...",
            "Marcus Cole (Macro Lead) evaluating institutional flows & sentiment...",
            "Vesper Sterling (Risk Lead) interrogating downside traps & stops...",
            "Sovereign AI (Consensus Node) resolving arguments & issuing final dossier..."
        ]
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
    document.getElementById("lblChartTitle").textContent = t.chartTitle;
    document.getElementById("lblRadarTitle").textContent = t.radarTitle;
    document.getElementById("lblArenaTitle").textContent = t.arenaTitle;
    document.getElementById("lblLgBull").textContent = t.lgBull;
    document.getElementById("lblLgBear").textContent = t.lgBear;
    document.getElementById("lblLgStop").textContent = t.lgStop;
    document.getElementById("lblFgTitle").textContent = t.lblFg;
    document.getElementById("lblStopTitle").textContent = t.lblStop;

    renderRadarTable();
    runAnalysis();
}

function switchCategory(cat) {
    currentCategory = cat;
    document.getElementById("tabCrypto").className = "segment-tab" + (cat === "CRYPTO" ? " active" : "");
    document.getElementById("tabStock").className = "segment-tab" + (cat === "EQUITY" ? " active" : "");
    
    renderPills();
    renderRadarTable();

    document.getElementById("symbolInput").value = cat === "CRYPTO" ? "BTC" : "NVDA";
    runAnalysis();
}

function renderPills() {
    const container = document.getElementById("pillsContainer");
    container.innerHTML = "";
    const list = currentCategory === "CRYPTO" ? COIN_LIST : STOCK_LIST;
    list.forEach(item => {
        const btn = document.createElement("button");
        btn.className = "pill" + (item.s === currentSymbol ? " active" : "");
        btn.textContent = item.s;
        btn.onclick = () => {
            document.getElementById("symbolInput").value = item.s;
            runAnalysis();
        };
        container.appendChild(btn);
    });
}

function renderRadarTable() {
    const tbody = document.getElementById("radarTbody");
    tbody.innerHTML = "";
    const list = currentCategory === "CRYPTO" ? COIN_LIST : STOCK_LIST;
    list.forEach(item => {
        const tr = document.createElement("tr");
        const cur = currentCategory === "CRYPTO" ? "$" : (item.s.includes("THYAO") || item.s.includes("ASELS") || item.s.includes("EREGL") ? "₺" : "$");
        const chgColor = item.c >= 0 ? "var(--green)" : "var(--red)";
        tr.innerHTML = `
            <td><strong>${item.s}</strong></td>
            <td style="color: var(--text-muted);">${item.n}</td>
            <td><strong>${cur}${item.p.toLocaleString(undefined, {minimumFractionDigits: 2})}</strong></td>
            <td style="color: ${chgColor}; font-weight: 700;">${item.c >= 0 ? '+' : ''}${item.c.toFixed(2)}%</td>
            <td>${item.r}</td>
            <td><button class="pill" style="font-size: 11px;">Analiz ↗</button></td>
        `;
        tr.onclick = () => {
            document.getElementById("symbolInput").value = item.s;
            window.scrollTo({ top: 0, behavior: 'smooth' });
            runAnalysis();
        };
        tbody.appendChild(tr);
    });
}

async function runAnalysis() {
    const symInput = document.getElementById("symbolInput").value.trim().toUpperCase();
    if (!symInput) return;

    currentSymbol = symInput;
    renderPills();
    const rounds = document.getElementById("roundsSelect").value;
    const errAlert = document.getElementById("errorAlert");
    errAlert.style.display = "none";

    const sBar = document.getElementById("swarmStatusBar");
    const sMsg = document.getElementById("swarmStatusMsg");
    sBar.style.display = "flex";

    const t = I18N[currentLang];
    sMsg.textContent = t.steps[0];

    try {
        const url = `/api/analyze?symbol=${encodeURIComponent(symInput)}&asset_type=${currentCategory}&rounds=${rounds}&lang=${currentLang}`;
        const resp = await fetch(url);
        const data = await resp.json();

        if (!resp.ok) {
            errAlert.textContent = data.error || "Geçersiz sembol!";
            errAlert.style.display = "block";
            sBar.style.display = "none";
            return;
        }

        // Stepped simulation effect for agent sequencing
        sMsg.textContent = t.steps[1];
        await new Promise(r => setTimeout(r, 220));
        sMsg.textContent = t.steps[2];
        await new Promise(r => setTimeout(r, 220));
        sMsg.textContent = t.steps[3];
        await new Promise(r => setTimeout(r, 220));

        renderData(data);
    } catch (err) {
        errAlert.textContent = "Bağlantı hatası: " + err;
        errAlert.style.display = "block";
    } finally {
        sBar.style.display = "none";
    }
}

function renderData(data) {
    const v = data.verdict;
    const m = data.market_data;
    const ind = m.indicators;
    currentVerdict = v;
    currentCandles = m.candles || [];

    const isBull = v.final_stance.includes("BULL");
    const isBear = v.final_stance.includes("BEAR");
    const color = isBull ? "var(--green)" : (isBear ? "var(--red)" : "var(--yellow)");

    // Hero consensus banner
    const hero = document.getElementById("consensusHero");
    hero.style.borderLeftColor = color;
    
    let stanceDisplay = v.final_stance;
    if (currentLang === "tr") {
        if (v.final_stance === "STRONG_BULL") stanceDisplay = "GÜÇLÜ YÜKSELİŞ (STRONG BULL)";
        else if (v.final_stance === "BULLISH") stanceDisplay = "YÜKSELİŞ (BULLISH)";
        else if (v.final_stance === "NEUTRAL") stanceDisplay = "NÖTR / BEKLE (NEUTRAL)";
        else if (v.final_stance === "BEARISH") stanceDisplay = "DÜŞÜŞ (BEARISH)";
        else if (v.final_stance === "STRONG_BEAR") stanceDisplay = "GÜÇLÜ DÜŞÜŞ (STRONG BEAR)";
    }

    document.getElementById("verdictStance").textContent = `${stanceDisplay} &bull; %${v.confidence_score} Güven`;
    document.getElementById("verdictStance").style.color = color;
    document.getElementById("verdictThesis").textContent = v.primary_thesis;

    // Header values
    const cur = m.currency === "TRY" ? "₺" : "$";
    document.getElementById("chartAssetHeader").textContent = `${m.symbol} / ${m.currency}`;
    document.getElementById("chartPrice").textContent = `${cur}${m.current_price.toLocaleString(undefined, {minimumFractionDigits: 2})}`;
    const chgEl = document.getElementById("chartChange");
    chgEl.textContent = `${m.change_24h_pct >= 0 ? '+' : ''}${m.change_24h_pct.toFixed(2)}%`;
    chgEl.style.color = m.change_24h_pct >= 0 ? "var(--green)" : "var(--red)";

    // Gauges
    document.getElementById("valRSI").textContent = ind.rsi_14.toFixed(1);
    const rsiBar = document.getElementById("barRSI");
    rsiBar.style.width = `${Math.min(100, Math.max(0, ind.rsi_14))}%`;
    rsiBar.style.background = ind.rsi_14 > 70 ? "var(--red)" : (ind.rsi_14 < 30 ? "var(--green)" : "var(--cyan)");

    document.getElementById("valFG").textContent = m.fear_greed_score;
    const fgBar = document.getElementById("barFG");
    fgBar.style.width = `${m.fear_greed_score}%`;
    fgBar.style.background = m.fear_greed_score > 60 ? "var(--green)" : (m.fear_greed_score < 40 ? "var(--red)" : "var(--yellow)");

    document.getElementById("valSMA").textContent = ind.trend_50_200;
    document.getElementById("valInval").textContent = `${cur}${v.key_invalidation_level.toLocaleString(undefined, {minimumFractionDigits: 2})}`;

    // Render Canvas Chart
    drawCanvasChart(currentCandles, ind, v.key_invalidation_level, cur);

    // Render Debates with lively animated bubbles
    const arena = document.getElementById("debateArena");
    arena.innerHTML = "";

    v.debate_rounds.forEach(r => {
        const roundTitle = document.createElement("div");
        roundTitle.style.cssText = "font-size: 11px; color: var(--cyan); text-transform: uppercase; letter-spacing: 1px; font-weight: 800; margin: 10px 0 4px 0;";
        roundTitle.textContent = currentLang === 'tr' 
            ? `▶ Münazara Turu #${r.round_number} (${r.consensus_shift_notes})` 
            : `▶ Debate Round #${r.round_number} (${r.consensus_shift_notes})`;
        arena.appendChild(roundTitle);

        r.thoughts.forEach(t => {
            const isTBull = t.stance.includes("BULL");
            const isTBear = t.stance.includes("BEAR");
            const tColor = isTBull ? "var(--green)" : (isTBear ? "var(--red)" : "var(--yellow)");
            const icon = t.role === "TECHNICAL" ? "📐" : (t.role === "SENTIMENT" ? "📰" : "🛡️");

            const card = document.createElement("div");
            card.className = "agent-card";
            card.innerHTML = `
                <div class="agent-top">
                    <span class="agent-avatar">${icon}</span>
                    <div>
                        <div class="agent-name">${t.agent_name}</div>
                        <div class="agent-callsign">[${t.callsign}] &bull; ${t.role}</div>
                    </div>
                    <span class="agent-badge" style="background: ${tColor}22; color: ${tColor}; border: 1px solid ${tColor}55;">
                        ${t.stance} (%${Math.round(t.confidence * 100)})
                    </span>
                </div>
                <div class="agent-speech">"${t.thesis}"</div>
                <ul class="agent-ul">
                    ${t.key_points.map(p => `<li>${p}</li>`).join("")}
                    ${t.identified_risks.map(rk => `<li class="risk-li">⚠️ ${rk}</li>`).join("")}
                </ul>
            `;
            arena.appendChild(card);
        });
    });
}

function drawCanvasChart(candles, ind, stopLevel, curSym) {
    const canvas = document.getElementById("candleCanvas");
    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;

    const width = canvas.parentElement.clientWidth;
    const height = canvas.parentElement.clientHeight;

    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);

    if (!candles || candles.length === 0) return;

    ctx.clearRect(0, 0, width, height);

    // Determine min and max price
    const allPrices = candles.flatMap(c => [c.high, c.low]);
    if (stopLevel) allPrices.push(stopLevel);
    if (ind && ind.bollinger_upper) allPrices.push(ind.bollinger_upper, ind.bollinger_lower);

    const minPrice = Math.min(...allPrices) * 0.985;
    const maxPrice = Math.max(...allPrices) * 1.015;
    const priceRange = maxPrice - minPrice;

    const getY = p => height - ((p - minPrice) / priceRange) * (height - 40) - 20;

    // Draw Grid Lines
    ctx.strokeStyle = "#1e293b";
    ctx.lineWidth = 1;
    for (let i = 1; i <= 4; i++) {
        const y = (height / 5) * i;
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();

        const gridP = maxPrice - (i / 5) * priceRange;
        ctx.fillStyle = "#475569";
        ctx.font = "10px sans-serif";
        ctx.fillText(`${curSym}${gridP.toLocaleString(undefined, {maximumFractionDigits: 1})}`, 6, y - 4);
    }

    // Draw Stop Invalidation dashed line
    if (stopLevel) {
        const stopY = getY(stopLevel);
        ctx.save();
        ctx.strokeStyle = "#f87171";
        ctx.lineWidth = 1.5;
        ctx.setLineDash([6, 4]);
        ctx.beginPath();
        ctx.moveTo(0, stopY);
        ctx.lineTo(width, stopY);
        ctx.stroke();
        ctx.fillStyle = "#f87171";
        ctx.font = "bold 10px sans-serif";
        ctx.fillText(`🛑 STOP: ${curSym}${stopLevel.toLocaleString(undefined, {maximumFractionDigits: 2})}`, width - 130, stopY - 5);
        ctx.restore();
    }

    // Candle Dimensions
    const n = candles.length;
    const candleWidth = Math.max(4, (width / n) * 0.65);
    const gap = width / n;

    candles.forEach((c, i) => {
        const x = i * gap + gap / 2;
        const openY = getY(c.open);
        const closeY = getY(c.close);
        const highY = getY(c.high);
        const lowY = getY(c.low);

        const isBull = c.close >= c.open;
        const color = isBull ? "#10b981" : "#ef4444";

        // Wick
        ctx.strokeStyle = color;
        ctx.lineWidth = 1.2;
        ctx.beginPath();
        ctx.moveTo(x, highY);
        ctx.lineTo(x, lowY);
        ctx.stroke();

        // Body
        ctx.fillStyle = color;
        const bodyTop = Math.min(openY, closeY);
        const bodyHeight = Math.max(2, Math.abs(closeY - openY));
        ctx.fillRect(x - candleWidth / 2, bodyTop, candleWidth, bodyHeight);
    });
}

function downloadReport(fmt) {
    window.open(`/api/report/${fmt}?symbol=${encodeURIComponent(currentSymbol)}&asset_type=${currentCategory}&lang=${currentLang}`, '_blank');
}

window.addEventListener("DOMContentLoaded", () => {
    renderPills();
    renderRadarTable();
    runAnalysis();
});

window.addEventListener("resize", () => {
    if (currentCandles.length > 0 && currentVerdict) {
        const cur = currentCategory === "CRYPTO" ? "$" : "₺";
        drawCanvasChart(currentCandles, currentVerdict, currentVerdict.key_invalidation_level, cur);
    }
});
</script>

</body>
</html>
"""


class AlphaSwarmHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)

        if parsed.path in ("/", "/index.html"):
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
