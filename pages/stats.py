import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Statistics — Transaction Monitor", layout="wide")

st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background: #0E1117; }
    [data-testid="stHeader"] { background: #0E1117; border-bottom: 1px solid #1E2535; }
    [data-testid="stSidebar"] { background: #161B27; border-right: 1px solid #2D3748; }
    .block-container { padding-top: 3rem; padding-bottom: 4rem; }
    [data-testid="stMetric"] {
        background: #161B27;
        border: 1px solid #2D3748;
        border-radius: 5px;
        padding: 16px 20px;
    }
    [data-testid="stMetricLabel"] p { color: #8899AA; font-size: 12px; }
    [data-testid="stMetricValue"] { color: #E2E8F0; }
</style>
""", unsafe_allow_html=True)

API_URL = "http://localhost:8000"


@st.cache_data(ttl=30)
def fetch_alerts():
    try:
        r = requests.get(f"{API_URL}/alerts", timeout=5)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        return None
    except Exception:
        return None


# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<h1 style="color: #E2E8F0; font-size: 1.9rem; font-weight: 700; margin: 0 0 6px 0;
           letter-spacing: -0.02em;">
    Statistics
</h1>
<p style="color: #8899AA; font-size: 0.95rem; margin: 0 0 2rem 0;">
    Cost center alert distribution and review status
</p>
""", unsafe_allow_html=True)

# ── Fetch ──────────────────────────────────────────────────────────────────────
data = fetch_alerts()

if data is None:
    st.markdown("""
    <div style="border: 1px solid #2D3748; border-radius: 5px; padding: 20px; background: #161B27;">
        <div style="color: #E05A5A; font-size: 14px; font-weight: 600; margin-bottom: 8px;">
            API unreachable
        </div>
        <div style="color: #8899AA; font-size: 13px;">
            Start the FastAPI server:
            <code style="background: #0E1117; padding: 2px 7px; border-radius: 3px; color: #8899AA;">
                uvicorn frontend.main:app --reload
            </code>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

if not data:
    st.markdown("""
    <div style="border: 1px solid #2D3748; border-radius: 5px; padding: 40px; background: #161B27;
                text-align: center; color: #5A6A7A; font-size: 13px;">
        No alert data recorded yet.
    </div>
    """, unsafe_allow_html=True)
    st.stop()

df = pd.DataFrame(data)

# ── Sidebar: cost center filter ────────────────────────────────────────────────
all_centers = sorted(df["cost_center"].dropna().unique().tolist())

selected = st.sidebar.multiselect(
    "Cost Centers",
    options=all_centers,
    default=all_centers,
)

if not selected:
    st.markdown("""
    <div style="border: 1px solid #2D3748; border-radius: 5px; padding: 24px; background: #161B27;
                color: #5A6A7A; font-size: 13px;">
        Select at least one cost center in the sidebar.
    </div>
    """, unsafe_allow_html=True)
    st.stop()

df_f = df[df["cost_center"].isin(selected)]

# ── Metrics ────────────────────────────────────────────────────────────────────
total    = len(df_f)
pending  = int((df_f["reviewed"] == 0).sum())
reviewed = total - pending

m1, m2, m3 = st.columns(3)
m1.metric("Total Alerts", total)
m2.metric("Pending Review", pending)
m3.metric("Reviewed", reviewed)

st.markdown("<div style='margin-bottom: 2.5rem;'></div>", unsafe_allow_html=True)

# ── Bar chart: flagged amount by cost center ───────────────────────────────────
st.markdown("""
<p style="color: #5A6A7A; font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em;
          margin-bottom: 14px;">
    Flagged Amount by Cost Center
</p>
""", unsafe_allow_html=True)

chart_df = (
    df_f.groupby("cost_center")["amount"]
    .sum()
    .reset_index()
    .sort_values("amount", ascending=False)
)

fig = go.Figure(go.Bar(
    x=chart_df["cost_center"],
    y=chart_df["amount"],
    marker=dict(color="#4F8BF9", line=dict(width=0)),
    hovertemplate="<b>%{x}</b><br>R$ %{y:,.2f}<extra></extra>",
))

fig.update_layout(
    height=360,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=0, r=0, t=10, b=0),
    bargap=0.35,
    xaxis=dict(
        showgrid=False,
        zeroline=False,
        tickfont=dict(color="#8899AA", size=11),
        tickangle=-30,
    ),
    yaxis=dict(
        showgrid=True,
        gridcolor="#2D3748",
        gridwidth=1,
        zeroline=False,
        tickfont=dict(color="#5A6A7A", size=10),
        tickprefix="R$ ",
        tickformat=",.0f",
    ),
)

st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

st.markdown("<div style='margin-bottom: 2.5rem;'></div>", unsafe_allow_html=True)

# ── Table: grouped by cost center ─────────────────────────────────────────────
st.markdown("""
<p style="color: #5A6A7A; font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em;
          margin-bottom: 14px;">
    Breakdown by Cost Center
</p>
""", unsafe_allow_html=True)

tbl = (
    df_f.groupby("cost_center")
    .agg(
        Count=("transaction_id", "count"),
        Pending=("reviewed", lambda x: int((x == 0).sum())),
        Reviewed=("reviewed", lambda x: int(x.sum())),
        Mean_Dev_Pct=("deviation", lambda x: x.abs().mean() * 100),
    )
    .reset_index()
    .rename(columns={"cost_center": "Cost Center", "Mean_Dev_Pct": "Mean |Dev| (%)"})
    .sort_values("Count", ascending=False)
)

st.dataframe(
    tbl,
    column_config={
        "Mean |Dev| (%)": st.column_config.NumberColumn(
            "Mean |Dev| (%)",
            format="%.1f",
            help="Average absolute deviation from the cost center mean, as a percentage.",
        ),
    },
    hide_index=True,
    use_container_width=True,
)
