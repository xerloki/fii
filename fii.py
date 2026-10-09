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
    page_title="Meus FIIs",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

REFRESH_MS = 300_000  # 5 minutos
TZ = ZoneInfo("America/Sao_Paulo")

DEFAULT_TICKERS = [
    "VGHF11", "TRXF11", "HGRU11", "MXRF11",
    "JSAF11", "KNCR11", "HGLG11", "ALZR11",
    "XPML11", "BTLG11", "KNSC11", "VISC11",
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
        ("Média simples", pct_txt(avg), tone(avg), "todos os fundos"),
        ("Maior alta", pct_txt(best["pct_change"]), tone(best["pct_change"]), best["FII"]),
        ("Maior queda", pct_txt(worst["pct_change"]), tone(worst["pct_change"]), worst["FII"]),
        ("Em alta", f"{ups} de {len(dados)}", "flat", "fundos no período"),
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
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@500;600&display=swap" rel="stylesheet">
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
</style>
</head>
<body>
<div id="stage">
    <div class="cap" id="cap"></div>
    <svg id="chart"></svg>
    <div id="tip"></div>
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

    const BASE_ALPHA = reduceMotion ? 0 : 0.015;
    const sim = d3.forceSimulation(data)
        .alphaDecay(0.02)
        .velocityDecay(0.2)
        .alphaTarget(BASE_ALPHA);
    sim.stop(); // só inicia quando o gráfico tiver tamanho (abas ocultas têm largura 0)

    const node = svg.append('g').selectAll('g').data(data).join('g')
        .attr('class', 'bubble')
        .call(d3.drag().on('start', dragStart).on('drag', dragging).on('end', dragEnd))
        .on('pointerenter', showTip)
        .on('pointermove', showTip)
        .on('pointerleave', hideTip);

    node.append('circle')
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
        if (!w || !h) return;
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

        node.select('circle').attr('r', d => d.r);
        tTicker.style('font-size', d => Math.max(10, Math.min(18, d.r * 0.27)) + 'px');
        tPct.style('font-size', d => Math.max(9, Math.min(14, d.r * 0.2)) + 'px');

        sim.force('x', d3.forceX(W / 2).strength(0.04))
           .force('y', d3.forceY(H / 2).strength(0.04))
           .force('collide', d3.forceCollide(d => d.r + 3).strength(0.9).iterations(3));
        sim.alpha(first ? 1 : 0.6).restart();
        first = false;
    }

    sim.on('tick', () => {
        if (!W || !H) return;
        data.forEach(d => {
            if (!reduceMotion) {
                d.vx += (Math.random() - 0.5) * 0.08;
                d.vy += (Math.random() - 0.5) * 0.08;
            }
            d.x = Math.max(d.r, Math.min(W - d.r, d.x));
            d.y = Math.max(d.r, Math.min(H - d.r, d.y));
        });
        node.attr('transform', d => 'translate(' + d.x + ',' + d.y + ')');
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
        if (!event.active) sim.alphaTarget(0.1).restart();
        d.fx = d.x; d.fy = d.y;
    }
    function dragging(event, d) { d.fx = event.x; d.fy = event.y; }
    function dragEnd(event, d) {
        if (!event.active) sim.alphaTarget(BASE_ALPHA);
        d.fx = null; d.fy = null;
    }
</script>
</body>
</html>
"""


def render_bubbles(dados, label: str):
    if not dados:
        st.warning("Sem dados para exibir neste período.")
        return
    payload = {"items": dados, "label": label, "labelLower": label.lower()}
    html = BUBBLES_HTML.replace("__DATA_JSON__", json.dumps(payload, ensure_ascii=False))
    components.html(html, height=620, scrolling=False)
    st.markdown(
        '<div class="hint">O tamanho da bolha indica a intensidade da variação. '
        "Arraste para mover e toque em uma bolha para ver o preço.</div>",
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────────────────────
# Barra lateral
# ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Carteira")
    raw = st.text_area(
        "Fundos acompanhados",
        value="\n".join(DEFAULT_TICKERS),
        height=260,
        help="Um código por linha ou separados por vírgula. Ex.: MXRF11, HGLG11",
    )
    if st.button("Atualizar agora", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.caption(f"Atualização automática a cada {REFRESH_MS // 60_000} minutos.")

tickers = parse_tickers(raw)

# ──────────────────────────────────────────────────────────────
# Cabeçalho
# ──────────────────────────────────────────────────────────────
now = datetime.now(TZ)
is_open = market_status(now)

st.markdown(
    f"""
<div class="hdr">
    <div>
        <div class="hdr-title">Meus FIIs</div>
        <div class="hdr-sub">Variação de preço dos fundos da carteira</div>
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
if not tickers:
    st.info("Adicione ao menos um código de fundo na barra lateral para começar.")
    st.stop()

try:
    close = fetch_prices(tuple(f"{t}.SA" for t in tickers))
    periods, missing = build_periods(close, [f"{t}.SA" for t in tickers])
except Exception:
    st.error(
        "Não foi possível obter as cotações do Yahoo Finance agora. "
        "Use “Atualizar agora” na barra lateral ou tente novamente em instantes."
    )
    st.stop()

if not periods["1 Dia"]:
    st.error("Nenhum dos códigos informados retornou cotação. Confira se estão corretos.")
    st.stop()

if missing:
    st.warning("Sem dados para: " + ", ".join(m.removesuffix(".SA") for m in missing))

tabs = st.tabs(list(PERIODS))
for tab, label in zip(tabs, PERIODS):
    with tab:
        dados = periods[label]
        render_kpis(dados)
        render_bubbles(dados, label)
        render_ranking(dados)

last_day = close.dropna(how="all").index[-1]
st.markdown(
    f'<div class="foot">Último pregão com dados: {last_day:%d/%m/%Y}. '
    "Fonte: Yahoo Finance; as cotações podem ter atraso. "
    "Variação calculada sobre o preço de fechamento, sem considerar proventos. "
    "Conteúdo informativo, não é recomendação de investimento.</div>",
    unsafe_allow_html=True,
)
