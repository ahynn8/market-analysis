import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime
import os

st.set_page_config(
    page_title="KCC Glass | Intelligence Dashboard v2",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

api_key = os.environ.get("FRED_API_KEY", "a07f772300688605fceafe572a105fd6")

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #0d1117; color: #e6edf3; }
[data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
[data-testid="stSidebar"] * { color: #e6edf3 !important; }
[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }
.sidebar-title { font-size: 13px; font-weight: 700; color: #58a6ff !important; letter-spacing: 2px; text-transform: uppercase; padding: 8px 0 16px 0; border-bottom: 1px solid #30363d; margin-bottom: 16px; }
.sidebar-subtitle { font-size: 11px; color: #8b949e !important; margin-bottom: 20px; }
.kpi-card { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 18px 20px; }
.kpi-card.blue   { border-left: 3px solid #58a6ff; }
.kpi-card.green  { border-left: 3px solid #3fb950; }
.kpi-card.orange { border-left: 3px solid #d29922; }
.kpi-card.purple { border-left: 3px solid #bc8cff; }
.kpi-label { font-size: 11px; color: #8b949e; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 6px; }
.kpi-value { font-size: 28px; font-weight: 700; color: #e6edf3; line-height: 1.1; }
.kpi-delta-pos { font-size: 12px; color: #3fb950; margin-top: 4px; }
.kpi-delta-neg { font-size: 12px; color: #f85149; margin-top: 4px; }
.kpi-delta-neu  { font-size: 12px; color: #8b949e; margin-top: 4px; }
.section-card { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 20px; margin-bottom: 16px; }
.section-title { font-size: 14px; font-weight: 700; color: #e6edf3; margin-bottom: 4px; }
.section-sub   { font-size: 11px; color: #8b949e; margin-bottom: 14px; }
.dash-header { display: flex; align-items: baseline; gap: 12px; margin-bottom: 4px; }
.dash-title  { font-size: 20px; font-weight: 700; color: #e6edf3; }
.dash-subtitle { font-size: 13px; color: #8b949e; }
.page-title { font-size: 18px; font-weight: 700; color: #58a6ff; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 1px solid #30363d; }
.placeholder-box { background: #0d1117; border: 1px dashed #30363d; border-radius: 8px; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 300px; color: #30363d; font-size: 13px; gap: 8px; }
.status-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #3fb950; margin-right: 5px; animation: pulse 2s infinite; }
@keyframes pulse { 0%,100%{ opacity:1; } 50%{ opacity:0.4; } }
.lc-section { background: #161b22; border: 1px solid #30363d; border-radius: 10px; padding: 20px; margin-bottom: 16px; }
.lc-section-title { font-size: 13px; font-weight: 700; color: #58a6ff; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 14px; padding-bottom: 10px; border-bottom: 1px solid #30363d; }
.port-header { font-size: 12px; font-weight: 700; color: #58a6ff; text-align: center; padding: 6px 0; border-bottom: 1px solid #30363d; margin-bottom: 8px; }
.item-label { font-size: 12px; color: #e6edf3; font-weight: 500; padding: 4px 0; }
.subtotal-row { background: #21262d; border-radius: 6px; padding: 8px 10px; margin-top: 8px; font-size: 13px; font-weight: 700; color: #3fb950; }
[data-testid="stNumberInput"] label { color: #e6edf3 !important; font-size: 12px !important; }
[data-testid="stNumberInput"] input { background-color: #21262d !important; color: #e6edf3 !important; border: 1px solid #30363d !important; font-size: 12px !important; }
</style>
""", unsafe_allow_html=True)

# ── 함수 ─────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def get_fred(series_id, name):
    url = (f"https://api.stlouisfed.org/fred/series/observations"
           f"?series_id={series_id}&api_key={api_key}&file_type=json")
    r = requests.get(url)
    data = r.json()
    if 'observations' not in data:
        st.error(f"API 오류 ({series_id}): {data}")
        st.stop()
    df = pd.DataFrame(data['observations'])[['date', 'value']]
    df.columns = ['date', name]
    df['date'] = pd.to_datetime(df['date'])
    df[name] = pd.to_numeric(df[name], errors='coerce')
    return df

@st.cache_data(ttl=3600)
def get_exchange_rate():
    try:
        r = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5)
        return r.json()['rates'].get('KRW', 1350)
    except:
        return 1350

def latest(df, col): return df[col].dropna().iloc[-1]
def delta_pct(df, col, periods=1):
    s = df[col].dropna()
    if len(s) < periods + 1: return 0
    return (s.iloc[-1] - s.iloc[-1 - periods]) / s.iloc[-1 - periods] * 100
def delta_html(val, unit=""):
    sign = "▲" if val > 0 else ("▼" if val < 0 else "—")
    cls  = "kpi-delta-pos" if val > 0 else ("kpi-delta-neg" if val < 0 else "kpi-delta-neu")
    return f'<div class="{cls}">{sign} {abs(val):.1f}{unit}</div>'

def calc_landing_cost(invoice, reciprocal_on, reciprocal_rate,
                      mpf_on, mpf_rate, hmf_rate, base_duty_rate,
                      ocean_freight, busan_local, destination, surcharge,
                      sqft_per_cntr=24000):
    base_duty  = invoice * base_duty_rate
    reciprocal = invoice * reciprocal_rate if reciprocal_on else 0
    mpf_raw    = invoice * mpf_rate
    mpf        = max(33.58, min(651.50, mpf_raw)) if mpf_on else 0
    hmf        = invoice * hmf_rate
    total_tax  = base_duty + reciprocal + mpf + hmf
    rows = []
    ports = ["Miami, FL", "New York, NY", "Houston, TX", "LAX/LGB", "Savannah, GA"]
    for i, port in enumerate(ports):
        ood   = ocean_freight[i] + busan_local + destination[i]
        sur   = surcharge[i]
        total = ood + sur + total_tax
        rows.append({"Port": port, "O+O+D": ood, "Tax/Duty": total_tax,
                     "실비": sur, "Total": total, "$/Sqft": total / sqft_per_cntr})
    return rows, total_tax

# ── session_state 초기값 설정 ─────────────────────────────────
def init_session_state(usd_krw):
    defaults = {
        'lc_invoice':       30000,
        'lc_exchange':      int(usd_krw),
        'lc_sqft':          24000,
        'lc_rec_on':        True,
        'lc_rec_rate':      15.0,
        'lc_mpf_on':        False,
        'lc_mpf_rate':      0.3464,
        'lc_hmf_rate':      0.125,
        'lc_base_duty':     0.0,
        'lc_ocean':         [2090, 2050, 2500, 1423, 2250],
        'lc_busan':         195.78,
        'lc_dest':          [1021, 1145, 1528, 978, 1813],
        'lc_sur':           [1192, 1165, 1192, 1165, 1192],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ── 사이드바 ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-title">LVT Intelligence</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-subtitle">KCC Glass | Overseas Sales</div>', unsafe_allow_html=True)
    menu = st.radio("", ["🏠 Home", "🚢 Freight", "🏡 Housing", "📈 Macro", "💱 FX/Tariff", "🧮 Landing Cost"], label_visibility="collapsed")
    st.markdown("---")
    st.markdown(f'<span class="status-dot"></span><span style="font-size:11px;color:#8b949e;">FRED API 연결됨</span>', unsafe_allow_html=True)
    st.markdown(f'<span style="font-size:10px;color:#30363d;">Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M")}</span>', unsafe_allow_html=True)

# ── 데이터 로드 ───────────────────────────────────────────────
with st.spinner('데이터 불러오는 중...'):
    df_housing  = get_fred('HOUST',        '주택착공')
    df_mortgage = get_fred('MORTGAGE30US', '모기지금리')
    df_cpi      = get_fred('CPIAUCSL',     'CPI')
    df_fedfunds = get_fred('FEDFUNDS',     '기준금리')
    df_newsales = get_fred('HSN1F',        '신규주택판매')
    usd_krw     = get_exchange_rate()

init_session_state(usd_krw)

v_housing  = latest(df_housing,  '주택착공')
v_mortgage = latest(df_mortgage, '모기지금리')
v_cpi      = latest(df_cpi,      'CPI')
v_fedfunds = latest(df_fedfunds, '기준금리')
d_housing  = delta_pct(df_housing,  '주택착공')
d_mortgage = delta_pct(df_mortgage, '모기지금리')
d_cpi      = delta_pct(df_cpi,      'CPI')
d_fedfunds = delta_pct(df_fedfunds, '기준금리')

# ── 대시보드 헤더 ─────────────────────────────────────────────
st.markdown('<div class="dash-header"><span class="dash-title">LVT Intelligence Dashboard</span><span class="dash-subtitle">KCC Glass | Overseas Sales</span></div>', unsafe_allow_html=True)
st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)

# ── KPI 카드 4개 (모든 페이지 공통) ──────────────────────────
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(f'<div class="kpi-card blue"><div class="kpi-label">Housing Starts</div><div class="kpi-value">{v_housing:,.0f}K</div>{delta_html(d_housing, "%")}</div>', unsafe_allow_html=True)
with k2:
    st.markdown(f'<div class="kpi-card green"><div class="kpi-label">Mortgage Rate (30Y)</div><div class="kpi-value">{v_mortgage:.2f}%</div>{delta_html(d_mortgage, "%p")}</div>', unsafe_allow_html=True)
with k3:
    st.markdown(f'<div class="kpi-card orange"><div class="kpi-label">CPI Index</div><div class="kpi-value">{v_cpi:.1f}</div>{delta_html(d_cpi, "%")}</div>', unsafe_allow_html=True)
with k4:
    st.markdown(f'<div class="kpi-card purple"><div class="kpi-label">USD / KRW</div><div class="kpi-value">{usd_krw:,.0f}</div><div class="kpi-delta-neu">— ExchangeRate API</div></div>', unsafe_allow_html=True)

st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)

PORTS = ["Miami, FL", "New York, NY", "Houston, TX", "LAX/LGB", "Savannah, GA"]

# ════════════════════════════════════════════════
# 🏠 Home
# ════════════════════════════════════════════════
if menu == "🏠 Home":
    left, right = st.columns(2, gap="medium")
    with left:
        st.markdown('<div class="section-card"><div class="section-title">US Housing & Mortgage Rate</div><div class="section-sub">New Home Sales (K units) vs 30Y Rate (%)</div>', unsafe_allow_html=True)
        df_m = df_mortgage[df_mortgage['date'] >= '2019-01-01'].copy()
        df_h = df_newsales[df_newsales['date'] >= '2019-01-01'].copy()
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(x=df_h['date'], y=df_h['신규주택판매'], name='New Home Sales (K)', marker_color='#1f6feb', opacity=0.75, yaxis='y1'))
        fig1.add_trace(go.Scatter(x=df_m['date'], y=df_m['모기지금리'], name='Mortgage Rate (%)', line=dict(color='#f85149', width=2), yaxis='y2'))
        fig1.update_layout(paper_bgcolor='#161b22', plot_bgcolor='#161b22', font=dict(color='#8b949e', size=11), height=240,
            legend=dict(bgcolor='#161b22', bordercolor='#30363d', borderwidth=1, font=dict(color='#e6edf3', size=10), x=0, y=1.08, orientation='h'),
            margin=dict(l=0, r=0, t=30, b=0), xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(title='Sales (K)', zeroline=False, title_font=dict(color='#8b949e')),
            yaxis2=dict(title='Rate (%)', overlaying='y', side='right', zeroline=False, title_font=dict(color='#8b949e')), hovermode='x unified')
        st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="section-card"><div class="section-title">CPI & Fed Funds Rate</div><div class="section-sub">Macro Indicators — 2019 to Present</div>', unsafe_allow_html=True)
        df_c = df_cpi[df_cpi['date'] >= '2019-01-01'].copy()
        df_f = df_fedfunds[df_fedfunds['date'] >= '2019-01-01'].copy()
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=df_c['date'], y=df_c['CPI'], name='CPI', line=dict(color='#d29922', width=2), fill='tozeroy', fillcolor='rgba(210,153,34,0.08)', yaxis='y1'))
        fig2.add_trace(go.Scatter(x=df_f['date'], y=df_f['기준금리'], name='Fed Funds Rate (%)', line=dict(color='#bc8cff', width=2, dash='dot'), yaxis='y2'))
        fig2.update_layout(paper_bgcolor='#161b22', plot_bgcolor='#161b22', font=dict(color='#8b949e', size=11), height=240,
            legend=dict(bgcolor='#161b22', bordercolor='#30363d', borderwidth=1, font=dict(color='#e6edf3', size=10), x=0, y=1.08, orientation='h'),
            margin=dict(l=0, r=0, t=30, b=0), xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(title='CPI', zeroline=False, title_font=dict(color='#8b949e')),
            yaxis2=dict(title='Rate (%)', overlaying='y', side='right', zeroline=False, title_font=dict(color='#8b949e')), hovermode='x unified')
        st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)

    with left:
        # 메인 랜딩코스트 — session_state 값으로 계산
        st.markdown('<div class="section-card"><div class="section-title">Landing Cost Calculator</div><div class="section-sub">Auto-calculated by port · Landing Cost 탭에서 값 수정 가능</div>', unsafe_allow_html=True)
        col_inv, col_btn = st.columns([3, 1])
        with col_inv:
            invoice_home = st.number_input("Invoice", min_value=1000, max_value=1000000,
                                           value=st.session_state.lc_invoice, step=1000,
                                           label_visibility="collapsed", key="home_invoice")
            st.session_state.lc_invoice = invoice_home
        with col_btn:
            rec_home = st.toggle("Reciprocal", value=st.session_state.lc_rec_on, key="home_rec")
            st.session_state.lc_rec_on = rec_home

        rows_home, _ = calc_landing_cost(
            st.session_state.lc_invoice,
            st.session_state.lc_rec_on, st.session_state.lc_rec_rate / 100,
            st.session_state.lc_mpf_on, st.session_state.lc_mpf_rate / 100,
            st.session_state.lc_hmf_rate / 100, st.session_state.lc_base_duty / 100,
            st.session_state.lc_ocean, st.session_state.lc_busan,
            st.session_state.lc_dest, st.session_state.lc_sur,
            st.session_state.lc_sqft
        )
        min_t = min(r['Total'] for r in rows_home)
        max_t = max(r['Total'] for r in rows_home)
        def hl_home(row):
            tv = next(r['Total'] for r in rows_home if r['Port'] == row['Port'])
            if tv == min_t: return ['color: #3fb950; font-weight: bold'] * len(row)
            elif tv == max_t: return ['color: #f85149'] * len(row)
            return [''] * len(row)
        df_home = pd.DataFrame(rows_home).copy()
        df_home['O+O+D']    = df_home['O+O+D'].apply(lambda x: f"${x:,.0f}")
        df_home['Tax/Duty'] = df_home['Tax/Duty'].apply(lambda x: f"${x:,.0f}")
        df_home['실비']      = df_home['실비'].apply(lambda x: f"${x:,.0f}")
        df_home['Total']    = df_home['Total'].apply(lambda x: f"${x:,.0f}")
        df_home['$/Sqft']   = df_home['$/Sqft'].apply(lambda x: f"${x:.3f}")
        st.dataframe(df_home.style.apply(hl_home, axis=1), use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="section-card"><div class="section-title">Coming Soon</div><div class="section-sub">추가 모듈 준비 중</div>', unsafe_allow_html=True)
        st.markdown('<div class="placeholder-box"><span style="font-size:28px">📡</span><span>AI News / SCFI Trend</span><span style="font-size:11px">Module under development</span></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════
# 🚢 Freight
# ════════════════════════════════════════════════
elif menu == "🚢 Freight":
    st.markdown('<div class="page-title">🚢 Freight — SCFI / CCFI Trend</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-card"><div class="section-title">SCFI / CCFI Trend</div><div class="section-sub">Shanghai Containerized Freight Index — 개발 예정</div>', unsafe_allow_html=True)
    st.markdown('<div class="placeholder-box"><span style="font-size:40px">🚢</span><span style="font-size:15px">SCFI / CCFI 데이터 연동 예정</span><span style="font-size:12px">Freightos API 또는 SCFI 공식 데이터 연동 후 활성화</span></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════
# 🏡 Housing
# ════════════════════════════════════════════════
elif menu == "🏡 Housing":
    st.markdown('<div class="page-title">🏡 Housing — 미국 주택시장 상세</div>', unsafe_allow_html=True)
    left, right = st.columns(2, gap="medium")
    with left:
        st.markdown('<div class="section-card"><div class="section-title">US Housing & Mortgage Rate</div><div class="section-sub">New Home Sales vs 30Y Mortgage Rate</div>', unsafe_allow_html=True)
        df_m = df_mortgage[df_mortgage['date'] >= '2019-01-01'].copy()
        df_h = df_newsales[df_newsales['date'] >= '2019-01-01'].copy()
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(x=df_h['date'], y=df_h['신규주택판매'], name='New Home Sales (K)', marker_color='#1f6feb', opacity=0.75, yaxis='y1'))
        fig1.add_trace(go.Scatter(x=df_m['date'], y=df_m['모기지금리'], name='Mortgage Rate (%)', line=dict(color='#f85149', width=2), yaxis='y2'))
        fig1.update_layout(paper_bgcolor='#161b22', plot_bgcolor='#161b22', font=dict(color='#8b949e', size=11), height=320,
            legend=dict(bgcolor='#161b22', bordercolor='#30363d', borderwidth=1, font=dict(color='#e6edf3', size=10), x=0, y=1.08, orientation='h'),
            margin=dict(l=0, r=0, t=30, b=0), xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(title='Sales (K)', zeroline=False), yaxis2=dict(title='Rate (%)', overlaying='y', side='right', zeroline=False), hovermode='x unified')
        st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="section-card"><div class="section-title">Housing Starts 추이</div><div class="section-sub">Monthly Housing Starts — 전체 기간</div>', unsafe_allow_html=True)
        fig_hs = go.Figure()
        fig_hs.add_trace(go.Scatter(x=df_housing['date'], y=df_housing['주택착공'], line=dict(color='#58a6ff', width=2), fill='tozeroy', fillcolor='rgba(88,166,255,0.08)'))
        fig_hs.update_layout(paper_bgcolor='#161b22', plot_bgcolor='#161b22', font=dict(color='#8b949e', size=11), height=320,
            margin=dict(l=0, r=0, t=10, b=0), xaxis=dict(showgrid=False, zeroline=False), yaxis=dict(zeroline=False), showlegend=False, hovermode='x unified')
        st.plotly_chart(fig_hs, use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════
# 📈 Macro
# ════════════════════════════════════════════════
elif menu == "📈 Macro":
    st.markdown('<div class="page-title">📈 Macro — 거시경제 지표 상세</div>', unsafe_allow_html=True)
    left, right = st.columns(2, gap="medium")
    with left:
        st.markdown('<div class="section-card"><div class="section-title">CPI & Fed Funds Rate</div><div class="section-sub">2019 to Present</div>', unsafe_allow_html=True)
        df_c = df_cpi[df_cpi['date'] >= '2019-01-01'].copy()
        df_f = df_fedfunds[df_fedfunds['date'] >= '2019-01-01'].copy()
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=df_c['date'], y=df_c['CPI'], name='CPI', line=dict(color='#d29922', width=2), fill='tozeroy', fillcolor='rgba(210,153,34,0.08)', yaxis='y1'))
        fig2.add_trace(go.Scatter(x=df_f['date'], y=df_f['기준금리'], name='Fed Funds Rate (%)', line=dict(color='#bc8cff', width=2, dash='dot'), yaxis='y2'))
        fig2.update_layout(paper_bgcolor='#161b22', plot_bgcolor='#161b22', font=dict(color='#8b949e', size=11), height=320,
            legend=dict(bgcolor='#161b22', bordercolor='#30363d', borderwidth=1, font=dict(color='#e6edf3', size=10), x=0, y=1.08, orientation='h'),
            margin=dict(l=0, r=0, t=30, b=0), xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(title='CPI', zeroline=False), yaxis2=dict(title='Rate (%)', overlaying='y', side='right', zeroline=False), hovermode='x unified')
        st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="section-card"><div class="section-title">기준금리 추이</div><div class="section-sub">Fed Funds Rate — 전체 기간</div>', unsafe_allow_html=True)
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=df_fedfunds['date'], y=df_fedfunds['기준금리'], line=dict(color='#bc8cff', width=2), fill='tozeroy', fillcolor='rgba(188,140,255,0.08)'))
        fig3.update_layout(paper_bgcolor='#161b22', plot_bgcolor='#161b22', font=dict(color='#8b949e', size=11), height=320,
            margin=dict(l=0, r=0, t=10, b=0), xaxis=dict(showgrid=False, zeroline=False), yaxis=dict(zeroline=False), showlegend=False, hovermode='x unified')
        st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════
# 💱 FX/Tariff
# ════════════════════════════════════════════════
elif menu == "💱 FX/Tariff":
    st.markdown('<div class="page-title">💱 FX/Tariff — 환율 & 관세 현황</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-card"><div class="section-title">환율 & 관세 현황</div><div class="section-sub">USD/KRW 실시간 · Reciprocal Duty 현황</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("USD / KRW", f"{usd_krw:,.0f}", help="ExchangeRate API 실시간")
    with col2: st.metric("Reciprocal Duty", "15%", help="현재 적용 중인 상호관세율")
    with col3: st.metric("Base Duty (FTA)", "0%", help="한미 FTA 적용")
    st.markdown('</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════
# 🧮 Landing Cost
# ════════════════════════════════════════════════
elif menu == "🧮 Landing Cost":
    st.markdown('<div class="page-title">🧮 Landing Cost — 상세 계산기</div>', unsafe_allow_html=True)
    st.info("💡 여기서 입력한 값은 Home 탭 랜딩코스트 결과표에 자동 반영됩니다.")

    # Assumption + Tax
    col_left, col_right = st.columns(2, gap="large")
    with col_left:
        st.markdown('<div class="lc-section"><div class="lc-section-title">📋 Assumption</div>', unsafe_allow_html=True)
        container_type = st.selectbox("Container Type", ["20FT", "40FT"], key="lc_cntr_type")
        sqft = st.number_input("Avg Sqft/Container", min_value=1000, max_value=50000,
                               value=st.session_state.lc_sqft, step=100, key="lc_sqft_input")
        st.session_state.lc_sqft = sqft
        inv = st.number_input("Invoice Value (USD)", min_value=1000, max_value=1000000,
                              value=st.session_state.lc_invoice, step=1000, key="lc_inv_input")
        st.session_state.lc_invoice = inv
        exr = st.number_input("Exchange Rate (KRW/USD)", min_value=1000, max_value=2000,
                              value=st.session_state.lc_exchange, step=10, key="lc_exr_input")
        st.session_state.lc_exchange = exr
        base = st.number_input("Base Duty Rate (%)", min_value=0.0, max_value=100.0,
                               value=st.session_state.lc_base_duty, step=0.1,
                               help="FTA 적용 시 0%", key="lc_base_input")
        st.session_state.lc_base_duty = base
        st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="lc-section"><div class="lc-section-title">💰 Tax & Duty</div>', unsafe_allow_html=True)
        rec_on = st.toggle("Reciprocal Duty 적용", value=st.session_state.lc_rec_on, key="lc_rec_toggle")
        st.session_state.lc_rec_on = rec_on
        rec_r = st.number_input("Reciprocal Duty Rate (%)", min_value=0.0, max_value=100.0,
                                value=st.session_state.lc_rec_rate, step=0.1, key="lc_rec_r_input")
        st.session_state.lc_rec_rate = rec_r
        mpf_on = st.toggle("MPF 적용 (CO 보완시 Free)", value=st.session_state.lc_mpf_on, key="lc_mpf_toggle")
        st.session_state.lc_mpf_on = mpf_on
        mpf_r = st.number_input("MPF Rate (%)", min_value=0.0, max_value=10.0,
                                value=st.session_state.lc_mpf_rate, step=0.01,
                                help="Min $33.58 / Max $651.50", key="lc_mpf_r_input")
        st.session_state.lc_mpf_rate = mpf_r
        hmf_r = st.number_input("HMF Rate (%)", min_value=0.0, max_value=10.0,
                                value=st.session_state.lc_hmf_rate, step=0.001, key="lc_hmf_r_input")
        st.session_state.lc_hmf_rate = hmf_r
        st.markdown('</div>', unsafe_allow_html=True)

    # Ocean Freight (가로형)
    st.markdown('<div class="lc-section"><div class="lc-section-title">🚢 Ocean Freight (USD/CNTR)</div>', unsafe_allow_html=True)
    of_cols = st.columns([2] + [1]*5)
    with of_cols[0]: st.markdown('<div class="item-label">Freight Charge</div>', unsafe_allow_html=True)
    ocean_freight = []
    of_defaults = st.session_state.lc_ocean
    for i, port in enumerate(PORTS):
        with of_cols[i+1]:
            st.markdown(f'<div class="port-header">{port.split(",")[0]}</div>', unsafe_allow_html=True)
            v = st.number_input("USD", min_value=0, value=of_defaults[i], step=10, key=f"of_{i}", label_visibility="collapsed")
            ocean_freight.append(v)
    st.session_state.lc_ocean = ocean_freight
    st.markdown('</div>', unsafe_allow_html=True)

    # Busan Local
    st.markdown('<div class="lc-section"><div class="lc-section-title">🇰🇷 Busan Local (Origin KR)</div>', unsafe_allow_html=True)
    bl_items = [
        ("AMS (PER BL)", "USD", 35.0, 1.0),
        ("THC (Terminal Handling)", "KRW", 150000, 1000),
        ("ISPS", "USD", 0.0, 0.5),
        ("WF/PSM 포함", "KRW", 4763, 100),
        ("DOC Fee (₩50,000/BL)", "KRW", 50000, 1000),
        ("Seal Charge (₩10,000/CNTR)", "KRW", 10000, 1000),
    ]
    bl_vals = []
    for label, currency, default, step in bl_items:
        c1, c2 = st.columns([3, 2])
        with c1: st.markdown(f'<div class="item-label">{label} ({currency})</div>', unsafe_allow_html=True)
        with c2: v = st.number_input(label, min_value=0.0, value=float(default), step=float(step), key=f"bl_{label}", label_visibility="collapsed")
        bl_vals.append((v, currency))
    busan_usd = sum(v if c == "USD" else v / st.session_state.lc_exchange for v, c in bl_vals)
    st.session_state.lc_busan = busan_usd
    st.markdown(f'<div class="subtotal-row">Busan Local 합계: ${busan_usd:,.2f}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Destination (가로형)
    st.markdown('<div class="lc-section"><div class="lc-section-title">🇺🇸 Destination (US)</div>', unsafe_allow_html=True)
    dest_items = [
        ("DO Fee (PER BL)",            [65, 65, 65, 65, 65]),
        ("ISF Filing (PER BL)",         [40, 35, 40, 40, 40]),
        ("Customs Clearance (PER BL)", [100, 190, 100, 100, 100]),
        ("WFG",                         [0, 78, 0, 0, 0]),
        ("TMC/CTF",                     [0, 0, 0, 17, 0]),
        ("Trucking (Inland)",           [650, 850, 1600, 650, 1600]),
        ("Chassis (PER CNTR)",          [90, 90, 45, 90, 90]),
    ]
    dest_header = st.columns([2] + [1]*5)
    with dest_header[0]: st.markdown('<div class="item-label" style="color:#8b949e;font-size:11px;">항목</div>', unsafe_allow_html=True)
    for i, port in enumerate(PORTS):
        with dest_header[i+1]: st.markdown(f'<div class="port-header">{port.split(",")[0]}</div>', unsafe_allow_html=True)
    dest_totals = [0.0] * 5
    for label, defaults in dest_items:
        row_cols = st.columns([2] + [1]*5)
        with row_cols[0]: st.markdown(f'<div class="item-label">{label}</div>', unsafe_allow_html=True)
        for i in range(5):
            with row_cols[i+1]:
                v = st.number_input(f"{label}_{i}", min_value=0, value=defaults[i], step=5, key=f"dest_{label}_{i}", label_visibility="collapsed")
                dest_totals[i] += v
    st.session_state.lc_dest = dest_totals
    sub_cols = st.columns([2] + [1]*5)
    with sub_cols[0]: st.markdown('<div class="subtotal-row">합계</div>', unsafe_allow_html=True)
    for i in range(5):
        with sub_cols[i+1]: st.markdown(f'<div class="subtotal-row">${dest_totals[i]:,.0f}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 실비 (가로형)
    st.markdown('<div class="lc-section"><div class="lc-section-title">💼 실비 (Surcharge)</div>', unsafe_allow_html=True)
    sur_items = [
        ("Container Pre-pull",  [175, 175, 175, 175, 175]),
        ("Waiting Charge",      [80, 57, 100, 57, 83]),
        ("Chassis Split Charge",[150, 150, 95, 150, 132]),
        ("Yard Storage",        [50, 50, 50, 50, 50]),
        ("TRI Axle Chassis",    [0, 0, 75, 0, 0]),
        ("Overweight Charge",   [300, 300, 200, 300, 300]),
        ("Demurrage",           [300, 250, 280, 300, 277]),
        ("Detention",           [200, 170, 230, 200, 200]),
        ("Exam (랜덤/Est.)",    [0, 0, 0, 0, 0]),
    ]
    sur_header = st.columns([2] + [1]*5)
    with sur_header[0]: st.markdown('<div class="item-label" style="color:#8b949e;font-size:11px;">항목</div>', unsafe_allow_html=True)
    for i, port in enumerate(PORTS):
        with sur_header[i+1]: st.markdown(f'<div class="port-header">{port.split(",")[0]}</div>', unsafe_allow_html=True)
    sur_totals = [0.0] * 5
    for label, defaults in sur_items:
        row_cols = st.columns([2] + [1]*5)
        with row_cols[0]: st.markdown(f'<div class="item-label">{label}</div>', unsafe_allow_html=True)
        for i in range(5):
            with row_cols[i+1]:
                v = st.number_input(f"{label}_{i}", min_value=0, value=defaults[i], step=5, key=f"sur_{label}_{i}", label_visibility="collapsed")
                sur_totals[i] += v
    st.session_state.lc_sur = sur_totals
    sub_cols2 = st.columns([2] + [1]*5)
    with sub_cols2[0]: st.markdown('<div class="subtotal-row">합계</div>', unsafe_allow_html=True)
    for i in range(5):
        with sub_cols2[i+1]: st.markdown(f'<div class="subtotal-row">${sur_totals[i]:,.0f}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 결과 테이블
    rows, total_tax = calc_landing_cost(
        st.session_state.lc_invoice,
        st.session_state.lc_rec_on, st.session_state.lc_rec_rate / 100,
        st.session_state.lc_mpf_on, st.session_state.lc_mpf_rate / 100,
        st.session_state.lc_hmf_rate / 100, st.session_state.lc_base_duty / 100,
        ocean_freight, busan_usd, dest_totals, sur_totals,
        st.session_state.lc_sqft
    )
    min_total = min(r['Total'] for r in rows)
    max_total = max(r['Total'] for r in rows)

    st.markdown('<div class="section-card"><div class="section-title">📊 Landing Cost 결과</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-sub">Total Tax: ${total_tax:,.0f} &nbsp;|&nbsp; Invoice: ${st.session_state.lc_invoice:,} &nbsp;|&nbsp; Exchange Rate: {st.session_state.lc_exchange:,}</div>', unsafe_allow_html=True)

    def highlight_lc(row):
        tv = next(r['Total'] for r in rows if r['Port'] == row['Port'])
        if tv == min_total: return ['color: #3fb950; font-weight: bold'] * len(row)
        elif tv == max_total: return ['color: #f85149'] * len(row)
        return [''] * len(row)

    df_show = pd.DataFrame(rows).copy()
    df_show['O+O+D']    = df_show['O+O+D'].apply(lambda x: f"${x:,.0f}")
    df_show['Tax/Duty'] = df_show['Tax/Duty'].apply(lambda x: f"${x:,.0f}")
    df_show['실비']      = df_show['실비'].apply(lambda x: f"${x:,.0f}")
    df_show['Total']    = df_show['Total'].apply(lambda x: f"${x:,.0f}")
    df_show['$/Sqft']   = df_show['$/Sqft'].apply(lambda x: f"${x:.3f}")
    st.dataframe(df_show.style.apply(highlight_lc, axis=1), use_container_width=True, hide_index=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div style="text-align:center; font-size:10px; color:#30363d; margin-top:24px; padding-bottom:8px;">KCC Glass Intelligence Dashboard · Capstone Project 2026 · Data: FRED · ExchangeRate API</div>', unsafe_allow_html=True)