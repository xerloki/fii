
import json
import re
from datetime import datetime, time
from zoneinfo import ZoneInfo
 
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
from streamlit_autorefresh import st_autorefresh
 
# ──────────────────────────────────────────────────────────────
# Configuração
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Minha Carteira",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed",
)
 
REFRESH_MS = 300_000  # 5 minutos
TZ = ZoneInfo("America/Sao_Paulo")
 
DEFAULT_FIIS = [
    "VGHF11", "TRXF11", "HGRU11", "MXRF11",
    "JSAF11", "KNCR11", "HGLG11", "ALZR11",
    "XPML11", "BTLG11", "KNSC11", "VISC11",
]
 
DEFAULT_ACOES = [
    "ITUB4", "BBSE3", "BBAS3", "SBSP3",
    "ISAE4", "EGIE3", "CXSE3", "SAPR4",
]
 
# Pregões para trás em cada período
PERIODS = {"1 Dia": 1, "1 Semana": 5, "1 Mês": 21}
 
st_autorefresh(interval=REFRESH_MS, key="fii_refresh")
 
# ──────────────────────────────────────────────────────────────
# Estilo da página
# ──────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&display=swap');
 
:root {
    --bg: #0b1018;
    --surface: #101826;
    --line: #1f2b3d;
    --text: #e8edf4;
    --muted: #8794a8;
    --up: #2ecc8f;
    --down: #ff5d6c;
}
 
.stApp { background: var(--bg); color: var(--text); }
.stApp, .stApp button, .stApp textarea, .stApp input {
    font-family: 'IBM Plex Sans', system-ui, -apple-system, 'Segoe UI', sans-serif;
}
[data-testid="stHeader"] { background: transparent; }
footer, #MainMenu { visibility: hidden; }
.block-container { max-width: 1200px; padding: 2rem 1.5rem 3rem; }
[data-testid="stSidebar"] { background: #0e1520; border-right: 1px solid var(--line); }
 
/* Cabeçalho */
.hdr { display: flex; justify-content: space-between; align-items: flex-end;
       gap: 12px; flex-wrap: wrap; margin-bottom: 18px; }
.hdr-title { font-size: 1.7rem; font-weight: 600; letter-spacing: -0.01em; line-height: 1.1; }
.hdr-sub { color: var(--muted); font-size: .92rem; margin-top: 6px; }
.hdr-meta { display: flex; flex-direction: column; align-items: flex-end; gap: 6px;
            color: var(--muted); font-size: .8rem; }
.pill { display: inline-flex; align-items: center; gap: 7px; padding: 4px 11px;
        border: 1px solid var(--line); border-radius: 999px; color: var(--text); font-size: .8rem; }
.pill i { width: 7px; height: 7px; border-radius: 50%; background: var(--muted); display: block; }
.pill.open i { background: var(--up); }
 
/* Abas */
.stTabs [data-baseweb="tab-list"] { gap: 6px; border-bottom: 1px solid var(--line); }
.stTabs [data-baseweb="tab"] { height: 44px; padding: 0 16px; background: transparent;
                               color: var(--muted); border-radius: 8px 8px 0 0; }
.stTabs [aria-selected="true"] { color: var(--text) !important; }
.stTabs [data-baseweb="tab-highlight"] { background-color: var(--up) !important; }
.stTabs [data-baseweb="tab-border"] { display: none; }
 
/* Indicadores */
.kpis { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 16px 0 14px; }
.kpi { background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: 12px 14px; }
.kpi-l { color: var(--muted); font-size: .78rem; }
.kpi-v { font-size: 1.4rem; font-weight: 600; margin-top: 4px; font-variant-numeric: tabular-nums; }
.kpi-s { color: var(--muted); font-size: .76rem; margin-top: 2px; min-height: 1em; }
.up { color: var(--up); }
.down { color: var(--down); }
.flat { color: var(--text); }
 
/* Ranking */
.sec { font-size: 1rem; font-weight: 600; margin: 22px 0 10px; }
.rk { background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: 4px 16px; }
.rk-row { display: grid; grid-template-columns: 110px 1fr 76px; align-items: center;
          gap: 14px; padding: 10px 0; border-bottom: 1px solid var(--line); }
.rk-row:last-child { border-bottom: none; }
.rk-name b { font-weight: 600; display: block; }
.rk-name span { color: var(--muted); font-size: .76rem; font-variant-numeric: tabular-nums; }
.rk-track { height: 6px; background: #172131; border-radius: 3px; overflow: hidden; }
.rk-track i { display: block; height: 100%; border-radius: 3px; }
.rk-track i.up { background: var(--up); }
.rk-track i.down { background: var(--down); }
.rk-pct { text-align: right; font-weight: 600; font-variant-numeric: tabular-nums; }
 
.hint { color: var(--muted); font-size: .8rem; margin: 8px 2px 0; }
.foot { color: var(--muted); font-size: .76rem; margin-top: 26px; line-height: 1.5; }
 
/* Celular */
@media (max-width: 640px) {
    .block-container { padding: 1rem .85rem 2.5rem; }
    .hdr-title { font-size: 1.4rem; }
    .hdr-meta { align-items: flex-start; }
    .kpis { grid-template-columns: repeat(2, 1fr); }
    .kpi-v { font-size: 1.2rem; }
    .rk { padding: 2px 12px; }
    .rk-row { grid-template-columns: 84px 1fr 62px; gap: 10px; }
    .stTabs [data-baseweb="tab-list"] { gap: 0; }
    .stTabs [data-baseweb="tab"] { flex: 1; justify-content: center; padding: 0 6px; }
}
</style>
""",
    unsafe_allow_html=True,
)
 
# ──────────────────────────────────────────────────────────────
# Utilidades
# ──────────────────────────────────────────────────────────────
def brl(value: float) -> str:
    s = f"{value:,.2f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")
 
 
def pct_txt(value: float) -> str:
    return f"{value:+.2f}%".replace(".", ",")
 
 
def tone(value: float) -> str:
    if value > 0:
        return "up"
    if value < 0:
        return "down"
    return "flat"
 
 
def parse_tickers(raw: str) -> list[str]:
    """Aceita um por linha ou separados por vírgula; remove duplicados e inválidos."""
    seen, result = set(), []
    for item in re.split(r"[,\s;]+", raw.upper()):
        item = item.strip().removesuffix(".SA")
        if re.fullmatch(r"[A-Z0-9]{4,7}", item) and item not in seen:
            seen.add(item)
            result.append(item)
    return result
 
 
def market_status(now: datetime) -> bool:
    """Pregão regular da B3 (não considera feriados)."""
    return now.weekday() < 5 and time(10, 0) <= now.time() <= time(17, 55)
 
 
# ──────────────────────────────────────────────────────────────
# Dados
# ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=120, show_spinner=False)
def fetch_prices(tickers: tuple) -> pd.DataFrame:
    # auto_adjust=False: variação de preço puro, sem somar proventos ao retorno
    df = yf.download(
        list(tickers), period="3mo", auto_adjust=False, progress=False, threads=True
    )
    if df is None or df.empty:
        raise ValueError("Yahoo Finance não retornou dados.")
    close = df["Close"]
    if isinstance(close, pd.Series):
        close = close.to_frame(tickers[0])
    return close
 
 
def build_periods(close: pd.DataFrame, tickers: list[str]):
    result = {label: [] for label in PERIODS}
    missing = []
    for t in tickers:
        if t not in close.columns:
            missing.append(t)
            continue
        s = close[t].dropna()
        if len(s) < 2:
            missing.append(t)
            continue
        current = float(s.iloc[-1])
        for label, back in PERIODS.items():
            ref = float(s.iloc[-1 - back]) if len(s) > back else float(s.iloc[0])
            pct = round((current / ref - 1) * 100, 2)
            result[label].append(
                {
                    "FII": t.removesuffix(".SA"),
                    "Preco": round(current, 2),
                    "pct_change": pct,
                    "abs_change": abs(pct),
                }
            )
    return result, missing
 
 
# ──────────────────────────────────────────────────────────────
# Componentes visuais
# ──────────────────────────────────────────────────────────────
def render_kpis(dados):
    avg = sum(d["pct_change"] for d in dados) / len(dados)
    best = max(dados, key=lambda d: d["pct_change"])
    worst = min(dados, key=lambda d: d["pct_change"])
    ups = sum(1 for d in dados if d["pct_change"] > 0)
 
    cards = [
        ("Média simples", pct_txt(avg), tone(avg), "todos os ativos"),
        ("Maior alta", pct_txt(best["pct_change"]), tone(best["pct_change"]), best["FII"]),
        ("Maior queda", pct_txt(worst["pct_change"]), tone(worst["pct_change"]), worst["FII"]),
        ("Em alta", f"{ups} de {len(dados)}", "flat", "ativos no período"),
    ]
    html = "".join(
        f'<div class="kpi"><div class="kpi-l">{l}</div>'
        f'<div class="kpi-v {t}">{v}</div><div class="kpi-s">{s}</div></div>'
        for l, v, t, s in cards
    )
    st.markdown(f'<div class="kpis">{html}</div>', unsafe_allow_html=True)
 
 
def render_ranking(dados):
    ordered = sorted(dados, key=lambda d: d["pct_change"], reverse=True)
    peak = max(d["abs_change"] for d in ordered) or 1
    rows = []
    for d in ordered:
        t = tone(d["pct_change"])
        width = max(d["abs_change"] / peak * 100, 3)
        rows.append(
            f'<div class="rk-row">'
            f'<div class="rk-name"><b>{d["FII"]}</b><span>{brl(d["Preco"])}</span></div>'
            f'<div class="rk-track"><i class="{t}" style="width:{width:.1f}%"></i></div>'
            f'<div class="rk-pct {t}">{pct_txt(d["pct_change"])}</div>'
            f"</div>"
        )
    st.markdown('<div class="sec">Ranking do período</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="rk">{"".join(rows)}</div>', unsafe_allow_html=True)
 
 
BUBBLES_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js"></script>
<style>
    * { box-sizing: border-box; }
    html, body { margin: 0; height: 100%; background: transparent; overflow: hidden;
                 font-family: 'IBM Plex Sans', system-ui, -apple-system, 'Segoe UI', sans-serif; }
    #stage { position: absolute; inset: 0; border: 1px solid #1f2b3d; border-radius: 16px;
             background: #0e1520; overflow: hidden; }
    svg { position: absolute; inset: 0; width: 100%; height: 100%; display: block; }
    .cap { position: absolute; left: 14px; top: 12px; color: #8794a8; font-size: 12px; pointer-events: none; }
    .bubble { touch-action: none; cursor: grab; }
    .bubble:active { cursor: grabbing; }
    .bubble circle { filter: drop-shadow(0 0 10px rgba(0, 0, 0, .35)); }
    .bubble text { text-anchor: middle; pointer-events: none; font-variant-numeric: tabular-nums; }
    .t { fill: #f2f5fa; font-weight: 600; }
    .p { font-weight: 500; }
    #tip { position: absolute; left: 0; top: 0; opacity: 0; pointer-events: none; z-index: 5;
           background: #172131; border: 1px solid #2a3a52; border-radius: 10px;
           padding: 8px 11px; color: #e8edf4; font-size: 12px; line-height: 1.45;
           display: flex; flex-direction: column; white-space: nowrap;
           transition: opacity .12s ease; }
    #tip b { font-size: 13px; }
    #tip .u { color: #2ecc8f; } #tip .d { color: #ff5d6c; }
 
    /* Botão compartilhar */
    .btn { display: inline-flex; align-items: center; gap: 7px; cursor: pointer;
           font: 500 12px 'IBM Plex Sans', system-ui, sans-serif; color: #e8edf4;
           background: #172131; border: 1px solid #2a3a52; border-radius: 999px;
           padding: 7px 13px; transition: background .15s, border-color .15s; }
    .btn:hover { background: #1d2a3f; border-color: #3a4f6e; }
    .btn.primary { background: #2ecc8f; border-color: #2ecc8f; color: #06281b; font-weight: 600; }
    .btn.primary:hover { background: #4bdba3; }
    .btn svg { position: static; width: 14px; height: 14px; }
    #share { position: absolute; right: 12px; top: 10px; z-index: 4; }
 
    /* Pré-visualização da imagem */
    #modal { position: absolute; inset: 0; z-index: 10; display: none; flex-direction: column;
             align-items: center; justify-content: center; gap: 12px; padding: 14px;
             background: rgba(7, 11, 17, .88); backdrop-filter: blur(6px); }
    #modal.open { display: flex; }
    #preview { max-width: 100%; min-height: 0; flex: 1 1 auto; object-fit: contain;
               border-radius: 12px; box-shadow: 0 10px 40px rgba(0, 0, 0, .55); }
    .row { display: flex; gap: 8px; flex-wrap: wrap; justify-content: center; flex: 0 0 auto; }
</style>
</head>
<body>
<div id="stage">
    <div class="cap" id="cap"></div>
    <button class="btn" id="share" type="button" aria-label="Compartilhar imagem dos balões">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="M8.6 13.5l6.8 4M15.4 6.5l-6.8 4"/></svg>
        Compartilhar
    </button>
    <svg id="chart"></svg>
    <div id="tip"></div>
    <div id="modal">
        <img id="preview" alt="Imagem gerada dos balões">
        <div class="row">
            <button class="btn primary" id="dl" type="button">Baixar imagem</button>
            <button class="btn" id="sh" type="button" style="display:none">Enviar</button>
            <button class="btn" id="close" type="button">Fechar</button>
        </div>
    </div>
</div>
<script>
    const PAYLOAD = __DATA_JSON__;
    const data = PAYLOAD.items;
 
    const stage = document.getElementById('stage');
    const tip = document.getElementById('tip');
    document.getElementById('cap').textContent = 'Variação em ' + PAYLOAD.label;
 
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const UP = '46,204,143', DOWN = '255,93,108';
    const fmtBRL = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });
    const fmtPct = v => (v > 0 ? '+' : '') + v.toFixed(2).replace('.', ',') + '%';
    const rgb = d => d.pct_change >= 0 ? UP : DOWN;
 
    const svg = d3.select('#chart');
    const defs = svg.append('defs');
    function gradient(id, color) {
        const g = defs.append('radialGradient').attr('id', id);
        g.append('stop').attr('offset', '45%').attr('stop-color', 'rgb(' + color + ')').attr('stop-opacity', 0.04);
        g.append('stop').attr('offset', '100%').attr('stop-color', 'rgb(' + color + ')').attr('stop-opacity', 0.34);
    }
    gradient('gUp', UP);
    gradient('gDown', DOWN);
 
    // Movimento: o "alphaTarget" alto mantém a simulação sempre ativa
    const BASE_ALPHA = reduceMotion ? 0 : 0.05;
    const WANDER = 0.11;   // empurrão contínuo em direção que muda devagar
    const JITTER = 0.12;   // tremor aleatório
    const sim = d3.forceSimulation(data)
        .alphaDecay(0.02)
        .velocityDecay(0.16)
        .alphaTarget(BASE_ALPHA);
    sim.stop(); // só inicia quando o gráfico tiver tamanho (abas ocultas têm largura 0)
 
    data.forEach(d => {
        d.ang = Math.random() * Math.PI * 2;
        d.phase = Math.random() * Math.PI * 2;
    });
 
    const node = svg.append('g').selectAll('g').data(data).join('g')
        .attr('class', 'bubble')
        .call(d3.drag().on('start', dragStart).on('drag', dragging).on('end', dragEnd))
        .on('pointerenter', showTip)
        .on('pointermove', showTip)
        .on('pointerleave', hideTip);
 
    const circles = node.append('circle')
        .attr('fill', d => 'url(#' + (d.pct_change >= 0 ? 'gUp' : 'gDown') + ')')
        .attr('stroke', d => 'rgb(' + rgb(d) + ')')
        .attr('stroke-width', 1.5);
    const tTicker = node.append('text').attr('class', 't').attr('dy', '-0.1em').text(d => d.FII);
    const tPct = node.append('text').attr('class', 'p').attr('dy', '1.25em')
        .attr('fill', d => 'rgb(' + rgb(d) + ')').text(d => fmtPct(d.pct_change));
 
    let W = 0, H = 0, first = true;
 
    // Tamanho das bolhas se adapta à área disponível (celular ou desktop)
    function layout() {
        const w = stage.clientWidth, h = stage.clientHeight;
        if (!w || !h) { sim.stop(); return; }   // aba oculta: pausa para poupar CPU
        W = w; H = h;
 
        const n = data.length;
        const base = Math.sqrt((W * H * 0.5) / (Math.PI * n));
        const rMax = Math.min(base * 1.3, 120, Math.min(W, H) / 2.8);
        const rMin = Math.max(rMax * 0.45, 24);
        const maxPct = d3.max(data, d => d.abs_change) || 0.1;
        const scale = d3.scaleSqrt().domain([0, maxPct]).range([rMin, rMax]);
 
        data.forEach(d => {
            d.r = scale(d.abs_change);
            if (first) {
                d.x = W / 2 + (Math.random() - 0.5) * W * 0.5;
                d.y = H / 2 + (Math.random() - 0.5) * H * 0.5;
            }
        });
 
        circles.attr('r', d => d.r);
        tTicker.style('font-size', d => Math.max(10, Math.min(18, d.r * 0.27)) + 'px');
        tPct.style('font-size', d => Math.max(9, Math.min(14, d.r * 0.2)) + 'px');
 
        sim.force('x', d3.forceX(W / 2).strength(0.03))
           .force('y', d3.forceY(H / 2).strength(0.03))
           .force('collide', d3.forceCollide(d => d.r + 3).strength(0.9).iterations(3));
        sim.alpha(first ? 1 : 0.6).restart();
        first = false;
    }
 
    sim.on('tick', () => {
        if (!W || !H) return;
        const t = performance.now();
        data.forEach(d => {
            if (!reduceMotion) {
                // direção de "passeio" que gira lentamente: cada bolha flutua no seu ritmo
                d.ang += (Math.random() - 0.5) * 0.18;
                d.vx += Math.cos(d.ang) * WANDER + (Math.random() - 0.5) * JITTER;
                d.vy += Math.sin(d.ang) * WANDER + (Math.random() - 0.5) * JITTER;
            }
            // quica suavemente nas bordas
            if (d.x < d.r)     { d.x = d.r;     d.vx =  Math.abs(d.vx) * 0.8; d.ang = Math.PI - d.ang; }
            if (d.x > W - d.r) { d.x = W - d.r; d.vx = -Math.abs(d.vx) * 0.8; d.ang = Math.PI - d.ang; }
            if (d.y < d.r)     { d.y = d.r;     d.vy =  Math.abs(d.vy) * 0.8; d.ang = -d.ang; }
            if (d.y > H - d.r) { d.y = H - d.r; d.vy = -Math.abs(d.vy) * 0.8; d.ang = -d.ang; }
        });
        node.attr('transform', d => 'translate(' + d.x + ',' + d.y + ')');
        if (!reduceMotion) {
            // "respiração": a bolha pulsa levemente
            circles.attr('r', d => d.r * (1 + 0.03 * Math.sin(t / 700 + d.phase)));
        }
    });
 
    new ResizeObserver(layout).observe(stage);
 
    // Tooltip (passe o mouse ou toque na bolha)
    let tipTimer = null;
    function showTip(event, d) {
        clearTimeout(tipTimer);
        const cls = d.pct_change >= 0 ? 'u' : 'd';
        tip.innerHTML = '<b>' + d.FII + '</b><span>' + fmtBRL.format(d.Preco) + '</span>' +
            '<span class="' + cls + '">' + fmtPct(d.pct_change) + ' em ' + PAYLOAD.labelLower + '</span>';
        tip.style.opacity = 1;
        const box = stage.getBoundingClientRect();
        const tw = tip.offsetWidth, th = tip.offsetHeight;
        let x = event.clientX - box.left + 14;
        let y = event.clientY - box.top - th - 10;
        x = Math.min(Math.max(8, x), W - tw - 8);
        y = Math.min(Math.max(8, y), H - th - 8);
        tip.style.transform = 'translate(' + x + 'px,' + y + 'px)';
        if (event.pointerType === 'touch') tipTimer = setTimeout(hideTip, 2200);
    }
    function hideTip(event) {
        if (event && event.pointerType === 'touch') {
            clearTimeout(tipTimer);
            tipTimer = setTimeout(() => { tip.style.opacity = 0; }, 2200);
            return;
        }
        tip.style.opacity = 0;
    }
 
    function dragStart(event, d) {
        if (!event.active) sim.alphaTarget(0.12).restart();
        d.fx = d.x; d.fy = d.y;
    }
    function dragging(event, d) { d.fx = event.x; d.fy = event.y; }
    function dragEnd(event, d) {
        if (!event.active) sim.alphaTarget(BASE_ALPHA);
        d.fx = null; d.fy = null;
    }
 
    // ───────────────── Compartilhar: gera a imagem ─────────────────
    function roundRect(ctx, x, y, w, h, r) {
        ctx.beginPath();
        ctx.moveTo(x + r, y);
        ctx.arcTo(x + w, y, x + w, y + h, r);
        ctx.arcTo(x + w, y + h, x, y + h, r);
        ctx.arcTo(x, y + h, x, y, r);
        ctx.arcTo(x, y, x + w, y, r);
        ctx.closePath();
    }
 
    async function buildImage() {
        try {
            await Promise.all([
                document.fonts.load('600 40px "IBM Plex Sans"'),
                document.fonts.load('500 20px "IBM Plex Sans"'),
                document.fonts.load('400 20px "IBM Plex Sans"'),
            ]);
        } catch (e) {}
        const FONT = '"IBM Plex Sans", system-ui, -apple-system, "Segoe UI", sans-serif';
 
        // a imagem acompanha a proporção da área dos balões (celular = vertical)
        const k = 1400 / Math.max(W, H);
        const cw = Math.round(W * k), ch = Math.round(H * k);
        const pad = 48, headH = 190, footH = 112;
        const cvW = cw + pad * 2, cvH = headH + ch + footH;
        const u = Math.max(0.75, Math.min(1, cvW / 1500));
 
        const cv = document.createElement('canvas');
        cv.width = cvW; cv.height = cvH;
        const ctx = cv.getContext('2d');
 
        // fundo
        const bg = ctx.createLinearGradient(0, 0, 0, cvH);
        bg.addColorStop(0, '#0b1018'); bg.addColorStop(1, '#101826');
        ctx.fillStyle = bg; ctx.fillRect(0, 0, cvW, cvH);
        const glow = ctx.createRadialGradient(cvW * 0.85, 0, 0, cvW * 0.85, 0, cvW * 0.8);
        glow.addColorStop(0, 'rgba(46,204,143,0.10)'); glow.addColorStop(1, 'rgba(46,204,143,0)');
        ctx.fillStyle = glow; ctx.fillRect(0, 0, cvW, cvH);
 
        // cabeçalho
        const avg = data.reduce((s, d) => s + d.pct_change, 0) / data.length;
        const ups = data.filter(d => d.pct_change > 0).length;
        ctx.textAlign = 'left'; ctx.textBaseline = 'alphabetic';
        ctx.fillStyle = '#e8edf4';
        ctx.font = '600 ' + Math.round(54 * u) + 'px ' + FONT;
        ctx.fillText(PAYLOAD.title, pad, pad + 54 * u);
        ctx.fillStyle = '#8794a8';
        ctx.font = '400 ' + Math.round(24 * u) + 'px ' + FONT;
        ctx.fillText('Variação em ' + PAYLOAD.label + '  ·  ' + PAYLOAD.stamp, pad, pad + 54 * u + 40 * u);
        const sy = pad + 54 * u + 40 * u + 38 * u;
        ctx.font = '600 ' + Math.round(26 * u) + 'px ' + FONT;
        ctx.fillStyle = avg >= 0 ? '#2ecc8f' : '#ff5d6c';
        const avgTxt = 'Média ' + fmtPct(avg);
        ctx.fillText(avgTxt, pad, sy);
        const avgW = ctx.measureText(avgTxt).width;
        ctx.fillStyle = '#8794a8';
        ctx.font = '400 ' + Math.round(26 * u) + 'px ' + FONT;
        ctx.fillText('   ·   ' + ups + ' de ' + data.length + ' em alta', pad + avgW, sy);
 
        // painel dos balões
        const ox = pad, oy = headH;
        ctx.save();
        roundRect(ctx, ox, oy, cw, ch, 28);
        ctx.fillStyle = '#0e1520'; ctx.fill();
        ctx.lineWidth = 2; ctx.strokeStyle = '#1f2b3d'; ctx.stroke();
        ctx.clip();
 
        data.forEach(d => {
            const x = ox + d.x * k, y = oy + d.y * k, r = d.r * k, c = rgb(d);
            ctx.save();
            ctx.shadowColor = 'rgba(' + c + ',0.38)';
            ctx.shadowBlur = 34;
            const g = ctx.createRadialGradient(x, y, r * 0.45, x, y, r);
            g.addColorStop(0, 'rgba(' + c + ',0.05)');
            g.addColorStop(1, 'rgba(' + c + ',0.36)');
            ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2);
            ctx.fillStyle = g; ctx.fill();
            ctx.shadowBlur = 0;
            ctx.lineWidth = 1.5 * k; ctx.strokeStyle = 'rgb(' + c + ')'; ctx.stroke();
            ctx.restore();
 
            const fsT = Math.max(10, Math.min(18, d.r * 0.27)) * k;
            const fsP = Math.max(9, Math.min(14, d.r * 0.2)) * k;
            ctx.textAlign = 'center';
            ctx.fillStyle = '#f2f5fa';
            ctx.font = '600 ' + fsT + 'px ' + FONT;
            ctx.fillText(d.FII, x, y - 0.1 * fsT);
            ctx.fillStyle = 'rgb(' + c + ')';
            ctx.font = '500 ' + fsP + 'px ' + FONT;
            ctx.fillText(fmtPct(d.pct_change), x, y + 1.25 * fsP);
        });
        ctx.restore();
 
        // rodapé
        ctx.textAlign = 'left';
        ctx.fillStyle = '#8794a8';
        ctx.font = '400 ' + Math.round(20 * u) + 'px ' + FONT;
        ctx.fillText('Desenvolvido por @nazareno.rar', pad, oy + ch + 42 * u);
        ctx.fillStyle = '#5d6b80';
        ctx.font = '400 ' + Math.round(18 * u) + 'px ' + FONT;
        ctx.fillText('Fonte: Yahoo Finance · preço de fechamento, sem proventos · não é recomendação de investimento', pad, oy + ch + 74 * u);
 
        return new Promise(res => cv.toBlob(res, 'image/png'));
    }
 
    // ───────────────── Janela de pré-visualização ─────────────────
    const modal = document.getElementById('modal');
    const preview = document.getElementById('preview');
    const shBtn = document.getElementById('sh');
    let currentBlob = null, currentUrl = null, currentFile = null;
 
    function fileName() {
        const slug = PAYLOAD.title.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]+/g, '-');
        return slug + '-' + PAYLOAD.labelLower.replace(/[^a-z0-9]+/g, '-') + '.png';
    }
 
    async function openShare() {
        if (!W || !H) return;
        const btn = document.getElementById('share');
        btn.disabled = true;
        try {
            currentBlob = await buildImage();
            if (currentUrl) URL.revokeObjectURL(currentUrl);
            currentUrl = URL.createObjectURL(currentBlob);
            currentFile = new File([currentBlob], fileName(), { type: 'image/png' });
            preview.src = currentUrl;
            const canShare = navigator.canShare && navigator.canShare({ files: [currentFile] });
            shBtn.style.display = canShare ? 'inline-flex' : 'none';
            modal.classList.add('open');
        } finally {
            btn.disabled = false;
        }
    }
    function closeModal() { modal.classList.remove('open'); }
    function download() {
        const a = document.createElement('a');
        a.href = currentUrl; a.download = fileName();
        document.body.appendChild(a); a.click(); a.remove();
    }
    async function nativeShare() {
        try {
            await navigator.share({ files: [currentFile], title: PAYLOAD.title });
        } catch (err) {
            if (err && err.name !== 'AbortError') download();  // sem permissão no iframe: baixa
        }
    }
 
    document.getElementById('share').addEventListener('click', openShare);
    document.getElementById('close').addEventListener('click', closeModal);
    document.getElementById('dl').addEventListener('click', download);
    shBtn.addEventListener('click', nativeShare);
    modal.addEventListener('click', e => { if (e.target === modal) closeModal(); });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });
</script>
</body>
</html>
"""
 
 
def render_bubbles(dados, label: str, title: str):
    if not dados:
        st.warning("Sem dados para exibir neste período.")
        return
    payload = {
        "items": dados,
        "label": label,
        "labelLower": label.lower(),
        "title": title,
        "stamp": datetime.now(TZ).strftime("%d/%m/%Y %H:%M"),
    }
    html = BUBBLES_HTML.replace("__DATA_JSON__", json.dumps(payload, ensure_ascii=False))
    components.html(html, height=620, scrolling=False)
    st.markdown(
        '<div class="hint">Desenvolvido por @nazareno.rar. '
        "Arraste para mover, toque em uma bolha para ver o preço e use "
        "“Compartilhar” para gerar uma imagem.</div>",
        unsafe_allow_html=True,
    )
 
 
def render_section(tickers: list[str], title: str, empty_msg: str):
    """Mostra as abas de período (1 Dia / 1 Semana / 1 Mês) para uma lista de ativos."""
    if not tickers:
        st.info(empty_msg)
        return
 
    sa = [f"{t}.SA" for t in tickers]
    try:
        close = fetch_prices(tuple(sa))
        periods, missing = build_periods(close, sa)
    except Exception:
        st.error(
            "Não foi possível obter as cotações do Yahoo Finance agora. "
            "Use “Atualizar agora” na barra lateral ou tente novamente em instantes."
        )
        return
 
    if not periods["1 Dia"]:
        st.error("Nenhum dos códigos informados retornou cotação. Confira se estão corretos.")
        return
 
    if missing:
        st.warning("Sem dados para: " + ", ".join(m.removesuffix(".SA") for m in missing))
 
    tabs = st.tabs(list(PERIODS))
    for tab, label in zip(tabs, PERIODS):
        with tab:
            dados = periods[label]
            render_kpis(dados)
            render_bubbles(dados, label, title)
            render_ranking(dados)
 
    last_day = close.dropna(how="all").index[-1]
    st.markdown(
        f'<div class="foot">Último pregão com dados: {last_day:%d/%m/%Y}. '
        "Fonte: Yahoo Finance; as cotações podem ter atraso. "
        "Variação calculada sobre o preço de fechamento, sem considerar proventos. "
        "Conteúdo informativo, não é recomendação de investimento.</div>",
        unsafe_allow_html=True,
    )
 
 
# ──────────────────────────────────────────────────────────────
# Barra lateral
# ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Carteira")
    raw_fiis = st.text_area(
        "Fundos imobiliários",
        value="\n".join(DEFAULT_FIIS),
        height=240,
        key="raw_fiis",
        help="Um código por linha ou separados por vírgula. Ex.: MXRF11, HGLG11",
    )
    raw_acoes = st.text_area(
        "Ações",
        value="\n".join(DEFAULT_ACOES),
        height=180,
        key="raw_acoes",
        help="Um código por linha ou separados por vírgula. Ex.: ITUB4, BBAS3",
    )
    if st.button("Atualizar agora", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.caption(f"Atualização automática a cada {REFRESH_MS // 60_000} minutos.")
 
fiis = parse_tickers(raw_fiis)
acoes = parse_tickers(raw_acoes)
 
# ──────────────────────────────────────────────────────────────
# Cabeçalho
# ──────────────────────────────────────────────────────────────
now = datetime.now(TZ)
is_open = market_status(now)
 
st.markdown(
    f"""
<div class="hdr">
    <div>
        <div class="hdr-title">Minha Carteira</div>
        <div class="hdr-sub">Variação de preço dos fundos e ações acompanhados</div>
    </div>
    <div class="hdr-meta">
        <span class="pill {'open' if is_open else ''}"><i></i>{'Pregão aberto' if is_open else 'Fora do pregão'}</span>
        <span>Atualizado às {now:%H:%M}</span>
    </div>
</div>
""",
    unsafe_allow_html=True,
)
 
# ──────────────────────────────────────────────────────────────
# Conteúdo
# ──────────────────────────────────────────────────────────────
tab_fiis, tab_acoes = st.tabs(["FIIs", "Ações"])
 
with tab_fiis:
    render_section(
        fiis,
        "Meus FIIs",
        "Adicione ao menos um código de fundo na barra lateral para começar.",
    )
 
with tab_acoes:
    render_section(
        acoes,
        "Minhas Ações",
        "Adicione ao menos um código de ação na barra lateral para começar.",
    )
