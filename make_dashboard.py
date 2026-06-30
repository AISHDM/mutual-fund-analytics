"""
=============================================================
  Bluestock Fintech – Capstone Project I
  DAY 5 – Dashboard Development
  Author : Dheeraj (iamrealdheeraj16)
  Date   : 2026-06-29
=============================================================
  Builds 4-page interactive dashboard (Plotly equivalent of Power BI)
  Exports:
    • reports/dashboard/page1_industry_overview.png
    • reports/dashboard/page2_fund_performance.png
    • reports/dashboard/page3_investor_analytics.png
    • reports/dashboard/page4_sip_market_trends.png
    • reports/Dashboard.pdf
    • reports/bluestock_mf_dashboard.html  (interactive)
=============================================================
"""

import warnings, json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.gridspec as gridspec
from pathlib import Path

warnings.filterwarnings('ignore')
np.random.seed(42)

# ── Paths ────────────────────────────────────────────────────
BASE     = Path('.')
RAW      = BASE / 'data' / 'raw'
OUT      = BASE / 'reports'
DASH_DIR = OUT / 'dashboard'
for d in [OUT, DASH_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Bluestock Brand Colors ───────────────────────────────────
C_BLUE   = '#1f4e79'
C_LBLUE  = '#2e75b6'
C_ACCENT = '#00b0f0'
C_RED    = '#c00000'
C_GREEN  = '#70ad47'
C_GOLD   = '#ffc000'
C_GRAY   = '#7f7f7f'
C_BG     = '#f0f4f8'
TEMPLATE = 'plotly_white'
PALETTE  = [C_BLUE, C_LBLUE, C_ACCENT, C_GREEN, C_GOLD,
            C_RED, '#9dc3e6', '#a9d18e', '#ffe699', '#ff9999']

# ══════════════════════════════════════════════════════════════
# SYNTHETIC DATA
# ══════════════════════════════════════════════════════════════
FUND_HOUSES = ['SBI','HDFC','ICICI','Nippon','Axis',
               'Kotak','UTI','Mirae','DSP','Parag']
CATEGORIES  = ['Large Cap','Mid Cap','Small Cap','Flexi Cap',
                'ELSS','Debt','Hybrid','Index']
STATES = ['Maharashtra','Karnataka','Tamil Nadu','Delhi','Gujarat',
          'Rajasthan','West Bengal','Telangana','UP','Andhra Pradesh',
          'Madhya Pradesh','Kerala','Haryana','Punjab','Bihar']

months_4y = pd.date_range('2022-01','2025-12',freq='MS')
months_str = [d.strftime('%b %Y') for d in months_4y]
years      = [2022,2023,2024,2025]

# AUM by AMC (₹ Lakh Crores)
aum_amc = pd.DataFrame({
    'AMC': FUND_HOUSES,
    'AUM': [12.50,8.90,7.90,4.70,4.45,3.50,3.10,2.30,2.10,1.80]
})

# Industry AUM trend
aum_trend = pd.Series(
    np.linspace(39, 81, len(months_4y)) + np.random.normal(0,0.8,len(months_4y)),
    index=months_str)

# SIP inflow trend
sip_trend = np.linspace(11000,31002,len(months_4y)) + np.random.normal(0,300,len(months_4y))
sip_trend[-1] = 31002

# Nifty 50 index (base 100)
nifty_rets = np.random.normal(0.00038,0.009,len(months_4y))
nifty50 = 100 * np.cumprod(1+nifty_rets)

# Fund scorecard (40 funds)
n_funds = 40
fund_df = pd.DataFrame({
    'Fund'     : [f'{fh} {cat[:5]}'
                  for fh in FUND_HOUSES for cat in CATEGORIES[:4]],
    'House'    : [fh for fh in FUND_HOUSES for _ in range(4)],
    'Category' : [cat for _ in FUND_HOUSES for cat in CATEGORIES[:4]],
    'Return_1Y': np.random.normal(18,7,n_funds).round(2),
    'StdDev'   : np.random.uniform(8,22,n_funds).round(2),
    'AUM_Cr'   : np.random.lognormal(10,1,n_funds).round(0),
    'Sharpe'   : np.random.uniform(0.5,2.1,n_funds).round(3),
    'Score'    : np.random.uniform(30,95,n_funds).round(1),
    'Expense'  : np.random.uniform(0.3,1.8,n_funds).round(2),
})

# Investor transactions
n_txn = 3000
txn_df = pd.DataFrame({
    'State'   : np.random.choice(STATES, n_txn,
                  p=[0.16,0.10,0.09,0.14,0.09,0.05,0.06,0.07,
                     0.05,0.06,0.04,0.03,0.03,0.02,0.01]),
    'Type'    : np.random.choice(['SIP','Lumpsum','Redemption'],
                  n_txn, p=[0.60,0.25,0.15]),
    'Amount'  : np.random.lognormal(9,1,n_txn).round(0),
    'AgeGroup': np.random.choice(['18-25','26-35','36-45','46-55','55+'],
                  n_txn, p=[0.12,0.35,0.30,0.15,0.08]),
    'CityTier': np.random.choice(['T30','B30'], n_txn, p=[0.71,0.29]),
    'Month'   : np.random.choice(months_str, n_txn),
})

# Category inflow heatmap
cat_inflow = pd.DataFrame(
    {cat: np.linspace(b, b*1.6, len(months_4y)) + np.random.normal(0,b*0.1,len(months_4y))
     for cat,b in zip(CATEGORIES,[9000,4500,2500,3500,1800,2200,2000,1200])},
    index=months_str
)

print("✅ Synthetic data ready")

# ══════════════════════════════════════════════════════════════
# PAGE 1 — INDUSTRY OVERVIEW
# ══════════════════════════════════════════════════════════════
def build_page1():
    print("  Building Page 1 — Industry Overview...")
    fig = make_subplots(
        rows=3, cols=4,
        row_heights=[0.18, 0.41, 0.41],
        specs=[
            [{"type":"indicator"},{"type":"indicator"},
             {"type":"indicator"},{"type":"indicator"}],
            [{"colspan":2,"type":"scatter"},None,
             {"colspan":2,"type":"bar"},None],
            [{"colspan":4,"type":"bar"},None,None,None],
        ],
        vertical_spacing=0.08,
        horizontal_spacing=0.06,
        subplot_titles=('','','','',
            'Industry AUM Trend 2022–2025 (₹ Lakh Crores)',
            'Top 10 AMCs by AUM (₹ Lakh Crores)',
            'AUM by Fund Category (₹ Lakh Crores) — Latest Month')
    )

    # KPI Cards
    kpis = [
        ("Total AUM","₹81L Cr","+28%"),
        ("SIP Inflows","₹31K Cr","+182%"),
        ("Active Folios","26.12 Cr","+97%"),
        ("No. of Schemes","1,908","+12%"),
    ]
    for i,(title,val,delta) in enumerate(kpis):
        fig.add_trace(go.Indicator(
            mode='number+delta',
            value=float(val.replace('₹','').replace('L Cr','e5')
                        .replace('K Cr','e3').replace(' Cr','')
                        .replace(',','')),
            title={'text':f"<b>{title}</b>",'font':{'size':13}},
            number={'prefix':'','font':{'size':26,'color':C_BLUE}},
            delta={'reference':0,'valueformat':'.0f',
                   'increasing':{'color':C_GREEN}},
        ), row=1, col=i+1)

    # AUM Trend Line
    fig.add_trace(go.Scatter(
        x=months_str, y=aum_trend.values,
        mode='lines', fill='tozeroy',
        line=dict(color=C_BLUE,width=2.5),
        fillcolor='rgba(31,78,121,0.12)',
        name='AUM (₹L Cr)', showlegend=False
    ), row=2, col=1)

    # AMC Bar
    amc_sorted = aum_amc.sort_values('AUM')
    colors_amc = [C_RED if v==amc_sorted['AUM'].max() else C_LBLUE
                  for v in amc_sorted['AUM']]
    fig.add_trace(go.Bar(
        x=amc_sorted['AUM'], y=amc_sorted['AMC'],
        orientation='h', marker_color=colors_amc,
        text=[f'₹{v:.1f}L' for v in amc_sorted['AUM']],
        textposition='outside', showlegend=False
    ), row=2, col=3)

    # Category AUM Bar
    cat_aum = [9.2,5.1,3.8,4.9,2.2,8.5,4.1,3.5]
    fig.add_trace(go.Bar(
        x=CATEGORIES, y=cat_aum,
        marker_color=PALETTE[:len(CATEGORIES)],
        text=[f'₹{v}L' for v in cat_aum],
        textposition='outside', showlegend=False
    ), row=3, col=1)

    fig.update_layout(
        title=dict(
            text='<b>BLUESTOCK MUTUAL FUND ANALYTICS</b> — Industry Overview',
            font=dict(size=18,color=C_BLUE), x=0.5
        ),
        height=850, paper_bgcolor=C_BG,
        plot_bgcolor='white', font=dict(family='Arial'),
        margin=dict(t=100,b=40,l=40,r=40)
    )
    return fig

# ══════════════════════════════════════════════════════════════
# PAGE 2 — FUND PERFORMANCE
# ══════════════════════════════════════════════════════════════
def build_page2():
    print("  Building Page 2 — Fund Performance...")
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Risk vs Return Bubble Chart (Size = AUM)',
            'Fund Scorecard — Top 15 (Sortable)',
            'NAV vs Benchmark — Top 5 Funds (3Y, Base 100)',
            'Sharpe Ratio Ranking — Top 20'
        ),
        specs=[[{"type":"scatter"},{"type":"table"}],
               [{"type":"scatter"},{"type":"bar"}]],
        vertical_spacing=0.12, horizontal_spacing=0.08
    )

    # Scatter: Risk vs Return
    for cat in CATEGORIES[:5]:
        sub = fund_df[fund_df['Category']==cat]
        fig.add_trace(go.Scatter(
            x=sub['StdDev'], y=sub['Return_1Y'],
            mode='markers', name=cat,
            marker=dict(size=sub['AUM_Cr']/sub['AUM_Cr'].max()*40+8,
                        opacity=0.75),
            text=sub['Fund'],
            hovertemplate='<b>%{text}</b><br>Risk: %{x:.1f}%<br>Return: %{y:.1f}%'
        ), row=1, col=1)

    # Table: Scorecard
    top15 = fund_df.nlargest(15,'Score')[
        ['Fund','Category','Return_1Y','Sharpe','Score','Expense']
    ].round(2)
    fig.add_trace(go.Table(
        header=dict(
            values=['<b>Fund</b>','<b>Category</b>','<b>1Y Ret%</b>',
                    '<b>Sharpe</b>','<b>Score</b>','<b>TER%</b>'],
            fill_color=C_BLUE, font=dict(color='white',size=11),
            align='center', height=28
        ),
        cells=dict(
            values=[top15[c] for c in top15.columns],
            fill_color=[['white','#f0f4f8']*8],
            font=dict(size=10), align='center', height=24
        )
    ), row=1, col=2)

    # NAV vs Benchmark line chart
    biz = pd.date_range('2023-06-01','2026-06-01',freq='B')
    biz_str = [d.strftime('%Y-%m-%d') for d in biz]
    bench_r = np.random.normal(0.00038,0.009,len(biz))
    bench   = 100*np.cumprod(1+bench_r)
    fig.add_trace(go.Scatter(x=biz_str,y=bench.tolist(),
        name='Nifty 100',line=dict(color='black',width=2,dash='dot'),
        showlegend=True), row=2, col=1)
    colors_f = [C_BLUE,C_LBLUE,C_ACCENT,C_GREEN,C_GOLD]
    top5 = fund_df.nlargest(5,'Score')
    for i,(_, row_f) in enumerate(top5.iterrows()):
        r = np.random.normal(0.00048,0.011,len(biz))
        nav = 100*np.cumprod(1+r)
        fig.add_trace(go.Scatter(
            x=biz_str, y=nav.tolist(),
            name=row_f['Fund'][:18],
            line=dict(color=colors_f[i],width=1.8)
        ), row=2, col=1)

    # Sharpe bar
    sharpe_top = fund_df.nlargest(20,'Sharpe').sort_values('Sharpe')
    fig.add_trace(go.Bar(
        x=sharpe_top['Sharpe'], y=sharpe_top['Fund'],
        orientation='h',
        marker_color=[C_RED if v==sharpe_top['Sharpe'].max()
                      else C_LBLUE for v in sharpe_top['Sharpe']],
        showlegend=False,
        text=[f'{v:.2f}' for v in sharpe_top['Sharpe']],
        textposition='outside'
    ), row=2, col=2)

    fig.update_layout(
        title=dict(text='<b>BLUESTOCK</b> — Fund Performance Analytics',
                   font=dict(size=18,color=C_BLUE), x=0.5),
        height=900, paper_bgcolor=C_BG,
        plot_bgcolor='white', font=dict(family='Arial'),
        margin=dict(t=100,b=40,l=40,r=40)
    )
    fig.add_shape(type='line',x0=0.5,x1=0.5,y0=0,y1=1,
                  xref='paper',yref='paper',
                  line=dict(color=C_GRAY,width=1,dash='dot'))
    return fig

# ══════════════════════════════════════════════════════════════
# PAGE 3 — INVESTOR ANALYTICS
# ══════════════════════════════════════════════════════════════
def build_page3():
    print("  Building Page 3 — Investor Analytics...")
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Transaction Amount by State (₹ Crores)',
            'SIP / Lumpsum / Redemption Split',
            'Avg SIP Amount by Age Group (₹)',
            'Monthly Transaction Volume Trend'
        ),
        specs=[[{"type":"bar"},{"type":"pie"}],
               [{"type":"bar"},{"type":"scatter"}]],
        vertical_spacing=0.14, horizontal_spacing=0.1
    )

    # State bar
    state_amt = txn_df.groupby('State')['Amount'].sum().sort_values()/1e7
    state_top = state_amt.tail(12)
    colors_s  = [C_RED if v==state_top.max() else C_LBLUE
                 for v in state_top.values]
    fig.add_trace(go.Bar(
        x=state_top.values, y=state_top.index,
        orientation='h', marker_color=colors_s,
        text=[f'₹{v:.0f}Cr' for v in state_top.values],
        textposition='outside', showlegend=False
    ), row=1, col=1)

    # Donut
    type_split = txn_df['Type'].value_counts()
    fig.add_trace(go.Pie(
        labels=type_split.index, values=type_split.values,
        hole=0.55, marker_colors=[C_BLUE,C_LBLUE,C_RED],
        textinfo='label+percent',
        hovertemplate='%{label}: %{value:,} txns<extra></extra>'
    ), row=1, col=2)

    # Age group avg SIP
    age_sip = txn_df[txn_df['Type']=='SIP'].groupby('AgeGroup')['Amount'].mean()
    age_order = ['18-25','26-35','36-45','46-55','55+']
    age_sip = age_sip.reindex(age_order)
    fig.add_trace(go.Bar(
        x=age_order, y=age_sip.values,
        marker_color=PALETTE[:5],
        text=[f'₹{v:,.0f}' for v in age_sip.values],
        textposition='outside', showlegend=False
    ), row=2, col=1)

    # Monthly volume line
    monthly_vol = txn_df.groupby('Month')['Amount'].sum().reindex(months_str).fillna(0)/1e7
    fig.add_trace(go.Scatter(
        x=months_str, y=monthly_vol.values,
        mode='lines+markers',
        line=dict(color=C_BLUE,width=2.5),
        marker=dict(size=5), showlegend=False
    ), row=2, col=2)

    # T30 vs B30 annotation
    t30 = txn_df[txn_df['CityTier']=='T30']['Amount'].sum()
    b30 = txn_df[txn_df['CityTier']=='B30']['Amount'].sum()
    total = t30+b30
    fig.add_annotation(
        text=f"<b>City Tier Split</b><br>T30: {t30/total*100:.0f}%   B30: {b30/total*100:.0f}%",
        xref='paper',yref='paper', x=0.78,y=0.52,
        showarrow=False, bgcolor='white',
        bordercolor=C_BLUE, borderwidth=1.5,
        font=dict(size=11,color=C_BLUE)
    )

    fig.update_layout(
        title=dict(text='<b>BLUESTOCK</b> — Investor Analytics',
                   font=dict(size=18,color=C_BLUE), x=0.5),
        height=880, paper_bgcolor=C_BG,
        plot_bgcolor='white', font=dict(family='Arial'),
        margin=dict(t=100,b=40,l=40,r=40)
    )
    return fig

# ══════════════════════════════════════════════════════════════
# PAGE 4 — SIP & MARKET TRENDS
# ══════════════════════════════════════════════════════════════
def build_page4():
    print("  Building Page 4 — SIP & Market Trends...")
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'SIP Inflow (Bar) vs Nifty 50 (Line) 2022–2025',
            'Category Inflow Heatmap (₹ Crores)',
            'Top 5 Categories by Net Inflow FY2025',
            'SIP Growth Rate YoY (%)'
        ),
        specs=[[{"secondary_y":True},
                {"type":"heatmap"}],
               [{"type":"bar"},{"type":"bar"}]],
        vertical_spacing=0.14, horizontal_spacing=0.10
    )

    # Dual-axis: SIP bar + Nifty line
    fig.add_trace(go.Bar(
        x=months_str, y=sip_trend,
        name='SIP Inflow (₹ Cr)',
        marker_color=C_LBLUE, opacity=0.8
    ), row=1, col=1, secondary_y=False)
    fig.add_trace(go.Scatter(
        x=months_str, y=nifty50.tolist(),
        name='Nifty 50 (Base 100)',
        line=dict(color=C_RED,width=2.5),
        mode='lines'
    ), row=1, col=1, secondary_y=True)

    # Heatmap (subset for clarity)
    heat_sub = cat_inflow.iloc[::3]   # every 3rd month
    heat_labels = list(heat_sub.index)
    fig.add_trace(go.Heatmap(
        z=heat_sub.values.T.tolist(),
        x=heat_labels,
        y=list(cat_inflow.columns),
        colorscale='YlOrRd',
        showscale=True,
        hovertemplate='%{y}<br>%{x}<br>₹%{z:,.0f} Cr<extra></extra>'
    ), row=1, col=2)

    # Top 5 categories FY25
    fy25_months = [m for m in months_str if '2025' in m]
    fy25_inflow = cat_inflow.loc[
        [m for m in fy25_months if m in cat_inflow.index]
    ].sum().nlargest(5)
    fig.add_trace(go.Bar(
        x=fy25_inflow.index, y=fy25_inflow.values/1000,
        marker_color=PALETTE[:5],
        text=[f'₹{v/1000:.1f}K Cr' for v in fy25_inflow.values],
        textposition='outside', name='FY25 Inflow',
        showlegend=False
    ), row=2, col=1)

    # YoY SIP growth
    yearly_sip = {}
    for yr in years:
        mask = [m for m in months_str if str(yr) in m]
        idx  = [months_str.index(m) for m in mask]
        yearly_sip[yr] = sip_trend[idx].mean()
    yoy_growth = {yr: (yearly_sip[yr]/yearly_sip.get(yr-1,yearly_sip[yr])-1)*100
                  for yr in years}
    fig.add_trace(go.Bar(
        x=[str(y) for y in years],
        y=[yoy_growth[y] for y in years],
        marker_color=[C_GREEN if v>0 else C_RED
                      for v in yoy_growth.values()],
        text=[f'{v:.1f}%' for v in yoy_growth.values()],
        textposition='outside', showlegend=False
    ), row=2, col=2)

    fig.add_annotation(
        text="₹31,002 Cr<br>All-Time High",
        x=months_str[-1], y=sip_trend[-1],
        xref='x', yref='y',
        showarrow=True, arrowhead=2,
        font=dict(color=C_RED, size=10, family='Arial Black'),
        bgcolor='white', bordercolor=C_RED, ax=40, ay=-50
    )

    fig.update_layout(
        title=dict(text='<b>BLUESTOCK</b> — SIP & Market Trends',
                   font=dict(size=18,color=C_BLUE), x=0.5),
        height=880, paper_bgcolor=C_BG,
        plot_bgcolor='white', font=dict(family='Arial'),
        margin=dict(t=100,b=40,l=40,r=40),
        legend=dict(x=0.01, y=0.97)
    )
    return fig

# ══════════════════════════════════════════════════════════════
# EXPORT FUNCTIONS
# ══════════════════════════════════════════════════════════════
def save_png(fig, name):
    path = DASH_DIR / name
    try:
        fig.write_image(str(path), scale=2, width=1400, height=900)
    except Exception as e:
        if 'Chrome' in str(e):
            print("  ⏳  Installing Chrome for kaleido (one-time setup)...")
            import subprocess
            subprocess.run(['plotly_get_chrome', '-y'], check=False)
            fig.write_image(str(path), scale=2, width=1400, height=900)
        else:
            raise
    kb = path.stat().st_size // 1024
    print(f"  💾  {name}  ({kb} KB)")
    return path

def build_html(figs):
    """Combine all 4 pages into one interactive HTML file."""
    from plotly.io import to_html
    parts = []
    titles = ['Page 1 — Industry Overview',
              'Page 2 — Fund Performance',
              'Page 3 — Investor Analytics',
              'Page 4 — SIP & Market Trends']
    for title, fig in zip(titles, figs):
        html = to_html(fig, full_html=False, include_plotlyjs='cdn'
                       if parts==[] else False)
        parts.append(f'<h2 style="color:{C_BLUE};font-family:Arial;'
                     f'padding:20px 20px 0">{title}</h2>{html}')

    full_html = f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<title>Bluestock MF Dashboard</title>
<style>
  body{{margin:0;background:#f0f4f8;font-family:Arial,sans-serif}}
  .header{{background:{C_BLUE};color:white;padding:18px 30px;
           font-size:22px;font-weight:bold;
           display:flex;align-items:center;gap:16px}}
  .nav{{background:{C_LBLUE};padding:10px 30px;display:flex;gap:20px}}
  .nav a{{color:white;text-decoration:none;font-weight:bold;
          font-size:13px;padding:6px 14px;border-radius:4px;
          background:rgba(255,255,255,0.15)}}
  .nav a:hover{{background:rgba(255,255,255,0.3)}}
  .section{{margin:0 20px 30px}}
</style>
</head>
<body>
<div class="header">
  🏦 Bluestock Fintech — Mutual Fund Analytics Dashboard
  <span style="font-size:13px;font-weight:normal;margin-left:auto">
    Capstone Project I | Dheeraj (iamrealdheeraj16)
  </span>
</div>
<div class="nav">
  <a href="#page1">📊 Industry Overview</a>
  <a href="#page2">🏆 Fund Performance</a>
  <a href="#page3">👥 Investor Analytics</a>
  <a href="#page4">📈 SIP & Market Trends</a>
</div>
{''.join(f'<div class="section" id="page{i+1}">{p}</div>'
          for i,p in enumerate(parts))}
</body></html>"""

    html_path = OUT / 'bluestock_mf_dashboard.html'
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(full_html)
    kb = html_path.stat().st_size // 1024
    print(f"  💾  bluestock_mf_dashboard.html  ({kb} KB)")
    return html_path

def build_pdf(png_paths):
    """Create multi-page PDF from PNG screenshots."""
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.platypus import (SimpleDocTemplate, Image, Spacer,
                                     Paragraph, PageBreak)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm

    pdf_path = OUT / 'Dashboard.pdf'
    doc = SimpleDocTemplate(str(pdf_path), pagesize=landscape(A4),
                            leftMargin=1.5*cm, rightMargin=1.5*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('T', parent=styles['Title'],
                                  textColor=colors.HexColor(C_BLUE),
                                  fontSize=16, spaceAfter=8)
    sub_style   = ParagraphStyle('S', parent=styles['Normal'],
                                  textColor=colors.gray,
                                  fontSize=9, spaceAfter=6)

    page_titles = [
        'Page 1 — Industry Overview',
        'Page 2 — Fund Performance Analytics',
        'Page 3 — Investor Analytics',
        'Page 4 — SIP & Market Trends',
    ]

    story = []
    # Cover
    story.append(Spacer(1, 2*cm))
    story.append(Paragraph(
        'Bluestock Fintech — Mutual Fund Analytics Dashboard',
        title_style))
    story.append(Paragraph(
        'Capstone Project I | Author: Dheeraj (iamrealdheeraj16) | Date: 2026-06-29',
        sub_style))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(
        'This dashboard presents comprehensive analytics across 40 mutual fund schemes '
        'covering industry AUM trends, fund performance metrics, investor demographics, '
        'and SIP market trends from 2022 to 2026.',
        styles['Normal']))
    story.append(PageBreak())

    # Pages
    pw = landscape(A4)[0] - 3*cm   # usable width
    for title, png_path in zip(page_titles, png_paths):
        if png_path.exists():
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 0.3*cm))
            img = Image(str(png_path), width=pw, height=pw*900/1400)
            story.append(img)
            story.append(PageBreak())

    doc.build(story)
    kb = pdf_path.stat().st_size // 1024
    print(f"  💾  Dashboard.pdf  ({kb} KB)")
    return pdf_path

# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print("\n" + "="*60)
    print("  BLUESTOCK — Day 5: Dashboard Development")
    print("="*60)

    print("\n📄 Building dashboard pages...")
    figs = [build_page1(), build_page2(), build_page3(), build_page4()]

    print("\n🖼️  Exporting PNGs...")
    png_names = ['page1_industry_overview.png',
                 'page2_fund_performance.png',
                 'page3_investor_analytics.png',
                 'page4_sip_market_trends.png']
    png_paths = [save_png(fig, name) for fig, name in zip(figs, png_names)]

    print("\n🌐 Building interactive HTML...")
    build_html(figs)

    print("\n📄 Building PDF...")
    build_pdf(png_paths)

    print("\n" + "="*60)
    print("  ✅  DASHBOARD COMPLETE")
    print("="*60)
    print(f"\n  Deliverables in reports/:")
    for f in sorted(OUT.rglob('*')):
        if f.is_file() and f.suffix in ['.png','.html','.pdf']:
            print(f"    • {f.relative_to(BASE)}  ({f.stat().st_size//1024} KB)")

    print("""
  📌 Power BI note (Mac users):
     Power BI Desktop is Windows-only. Two options:
     1. Upload bluestock_mf_dashboard.html to GitHub Pages
     2. Go to app.powerbi.com → New Report → Upload CSV files
        from data/processed/ and recreate visuals online
     The HTML dashboard above is a full equivalent deliverable.

  Next step:
    git add .
    git commit -m "Day 5: Dashboard complete — 4 pages, HTML + PDF"
    git push
""")
