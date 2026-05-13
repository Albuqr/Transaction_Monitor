import streamlit as st
import pandas as pd

st.set_page_config(page_title="Transaction Monitor", layout="wide")

# ── Font + theme ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
[data-testid="stAppViewContainer"] { background: #0E1117; }
[data-testid="stHeader"]           { background: #0E1117; border-bottom: 1px solid #1E2535; }
[data-testid="stSidebar"]          { background: #161B27; border-right:  1px solid #2D3748; }
.block-container { padding-top: 3rem; padding-bottom: 4rem; }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="color:#4F8BF9; font-size:11px; font-weight:600; letter-spacing:0.12em;
            text-transform:uppercase; margin-bottom:10px;">
    Real-Time Anomaly Detection System
</div>
<h1 style="color:#E2E8F0; font-size:2.1rem; font-weight:700; margin:0 0 8px 0;
           letter-spacing:-0.02em;">
    Transaction Monitor
</h1>
<p style="color:#8899AA; font-size:0.95rem; margin:0 0 1.8rem 0;">
    Real-time financial anomaly detection for manufacturing operations
</p>
""", unsafe_allow_html=True)

# ── Body paragraph ─────────────────────────────────────────────────────────────
st.markdown("""
<p style="color:#B0BAC4; font-size:0.9rem; line-height:1.8; max-width:820px;
          border-left:2px solid #2D3748; padding-left:18px; margin-bottom:3rem;">
    A Brazilian confectionery manufacturer with 28 production machines records all financial
    transactions manually. This system ingests those transactions through Kafka, compares them
    against rolling cost center baselines stored in Redis, and flags deviations beyond 20% for
    human review &#8212; in under 30 seconds.
</p>
""", unsafe_allow_html=True)

# ── Architecture ───────────────────────────────────────────────────────────────
st.markdown("""
<p style="color:#5A6A7A; font-size:11px; font-weight:600; text-transform:uppercase;
          letter-spacing:0.12em; margin-bottom:14px;">
    Architecture
</p>
""", unsafe_allow_html=True)

boxes = [
    ("Producer",      "Reads ERP exports", "#4F8BF9", "rgba(79, 139, 249, 0.15)"),
    ("Kafka (KRaft)", "Event streaming",   "#E31C1C", "rgba(227, 28, 28, 0.15)"),
    ("Consumer",      "Detects anomalies", "#4F8BF9", "rgba(79, 139, 249, 0.15)"),
    ("Redis",         "Rolling baselines", "#D82C20", "rgba(216, 44, 32, 0.15)"),
    ("SQLite",        "Alert storage",     "#0F80CC", "rgba(15, 128, 204, 0.15)"),
    ("FastAPI",       "REST layer",        "#009688", "rgba(0, 150, 136, 0.15)"),
    ("Streamlit",     "This dashboard",    "#FF4B4B", "rgba(255, 75, 75, 0.15)"),
]

cols = st.columns([5, 1, 5, 1, 5, 1, 5, 1, 5, 1, 5, 1, 5])

for i, (name, sub, border_color, bg_color) in enumerate(boxes):
    with cols[i * 2]:
        st.markdown(f"""
        <div style="border:1px solid {border_color}; border-radius:6px; padding:14px 10px;
                    text-align:center; background:{bg_color}; min-height:62px;
                    display:flex; flex-direction:column; justify-content:center; align-items:center;">
            <div style="color:#E2E8F0; font-weight:600; font-size:13px; line-height:1.3;">{name}</div>
            <div style="color:#8899AA; font-size:11px; margin-top:5px;">{sub}</div>
        </div>
        """, unsafe_allow_html=True)
    if i < len(boxes) - 1:
        with cols[i * 2 + 1]:
            st.markdown("""
            <div style="display:flex; align-items:center; justify-content:center;
                        min-height:62px; color:#3A4A5A; font-size:18px;">
                &#8594;
            </div>
            """, unsafe_allow_html=True)

st.markdown("<div style='margin-bottom:2.5rem;'></div>", unsafe_allow_html=True)

# ── Design Decisions ───────────────────────────────────────────────────────────
st.markdown("""
<p style="color:#5A6A7A; font-size:11px; font-weight:600; text-transform:uppercase;
          letter-spacing:0.12em; margin-bottom:14px;">
    Design Decisions
</p>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3, gap="large")

with c1:
    st.markdown("""
    <div style="border:1px solid #2D3748; border-radius:6px; padding:22px;
                background:#161B27; height:100%;">
        <div style="color:#E2E8F0; font-weight:600; font-size:14px; margin-bottom:10px;">
            Rule-based detection, not ML
        </div>
        <div style="color:#8899AA; font-size:13px; line-height:1.75;">
            Zero labeled anomaly history makes training impossible. A statistical threshold &#8212;
            flagging transactions beyond &#177;20% of each cost center&#39;s rolling mean &#8212; is
            deterministic, auditable, and effective from day one.
        </div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown("""
    <div style="border:1px solid #2D3748; border-radius:6px; padding:22px;
                background:#161B27; height:100%;">
        <div style="color:#E2E8F0; font-weight:600; font-size:14px; margin-bottom:10px;">
            Cost center granularity
        </div>
        <div style="color:#8899AA; font-size:13px; line-height:1.75;">
            ERP exports contain no supplier descriptions. Cost center codes are the finest level of
            specificity the source data supports; baselines and comparisons are built at this level.
        </div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown("""
    <div style="border:1px solid #2D3748; border-radius:6px; padding:22px;
                background:#161B27; height:100%;">
        <div style="color:#E2E8F0; font-weight:600; font-size:14px; margin-bottom:10px;">
            Data-honest design
        </div>
        <div style="color:#8899AA; font-size:13px; line-height:1.75;">
            The source data contained no supplier-level descriptions &#8212; the factory never recorded
            them. Rather than fabricating supplier mappings, the system operates at cost center
            granularity, the finest level the data actually supports. The gap is documented, not hidden.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='margin-bottom:2.5rem;'></div>", unsafe_allow_html=True)

# ── Tech Stack ─────────────────────────────────────────────────────────────────
st.markdown("""
<p style="color:#5A6A7A; font-size:11px; font-weight:600; text-transform:uppercase;
          letter-spacing:0.12em; margin-bottom:14px;">
    Tech Stack
</p>
""", unsafe_allow_html=True)

tech_data = {
    "Technology": [
        "Python 3.11",
        "Apache Kafka (KRaft)",
        "Redis",
        "SQLite",
        "FastAPI",
        "Streamlit",
        "BigQuery",
        "dbt",
    ],
    "Role": [
        "Core language",
        "Event streaming — no ZooKeeper dependency",
        "In-memory baseline storage per cost center",
        "Lightweight alert persistence",
        "REST API — /alerts, /resolutions",
        "This dashboard",
        "Historical data warehouse",
        "Bronze/silver/gold transformations",
    ],
}

st.dataframe(pd.DataFrame(tech_data), use_container_width=True, hide_index=True)

st.markdown("<div style='margin-bottom:2.5rem;'></div>", unsafe_allow_html=True)

# ── Connected systems ──────────────────────────────────────────────────────────
st.markdown("""
<p style="color:#5A6A7A; font-size:11px; font-weight:600; text-transform:uppercase;
          letter-spacing:0.12em; margin-bottom:14px;">
    Part of a Larger Platform
</p>
""", unsafe_allow_html=True)

st.markdown("""
<div style="border-left:3px solid #4F8BF9; border-radius:0 6px 6px 0;
            padding:20px 24px; background:#161B27;">
    <div style="color:#B0BAC4; font-size:13px; line-height:1.85;">
        This monitor is the second of three interconnected repositories built for the same client.
        The <span style="color:#E2E8F0; font-weight:600;">Factory Lakehouse (Repo 1)</span> ingests
        raw Excel data from 28 machines into BigQuery using dbt bronze/silver/gold transformations,
        orchestrated by Airflow. The
        <span style="color:#E2E8F0; font-weight:600;">Transaction Monitor (this repo)</span> sits on
        top of that data layer, streaming financial events through Kafka for real-time anomaly
        detection. A unified
        <span style="color:#E2E8F0; font-weight:600;">Platform API (Repo 3, in progress)</span> will
        wire both systems into a single dashboard with dependency inversion &#8212; so the presentation
        layer never talks directly to BigQuery or Kafka.
    </div>
</div>
""", unsafe_allow_html=True)
