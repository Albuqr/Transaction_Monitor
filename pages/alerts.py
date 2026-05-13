import streamlit as st
import requests
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Alert Review — Transaction Monitor", layout="wide")

st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background: #0E1117; }
    [data-testid="stHeader"] { background: #0E1117; border-bottom: 1px solid #1E2535; }
    [data-testid="stSidebar"] { background: #161B27; border-right: 1px solid #2D3748; }
    .block-container { padding-top: 3rem; padding-bottom: 4rem; }
</style>
""", unsafe_allow_html=True)

API_URL = "http://localhost:8000"


def fetch_alerts():
    try:
        r = requests.get(f"{API_URL}/alerts", timeout=5)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        return None
    except Exception:
        return None


def resolve_alert(transaction_id: str, is_legitimate: bool):
    r = requests.post(
        f"{API_URL}/resolutions",
        json={"transaction_id": transaction_id, "is_legitimate": is_legitimate},
        timeout=5,
    )
    return r.json()


def build_threshold_chart(amount: float, mean_val: float, dev_pct: float) -> go.Figure:
    lower = mean_val * 0.8
    upper = mean_val * 1.2
    bar_color = "#E05A5A" if dev_pct > 0 else "#4F8BF9"
    x_max = max(amount, upper, mean_val) * 1.18
    if x_max == 0:
        x_max = 1.0

    fig = go.Figure()

    if mean_val > 0:
        fig.add_vrect(
            x0=lower, x1=upper,
            fillcolor="rgba(72, 187, 120, 0.1)",
            line=dict(color="rgba(72, 187, 120, 0.45)", width=1),
        )

    fig.add_trace(go.Bar(
        x=[mean_val],
        y=["Mean"],
        orientation="h",
        marker=dict(color="#4A5568"),
        showlegend=False,
        hovertemplate="Mean: R$ %{x:,.2f}<extra></extra>",
    ))

    fig.add_trace(go.Bar(
        x=[amount],
        y=["Transaction"],
        orientation="h",
        marker=dict(color=bar_color),
        showlegend=False,
        hovertemplate="Transaction: R$ %{x:,.2f}<extra></extra>",
    ))

    if mean_val > 0:
        fig.add_annotation(
            x=lower, y=1.0, xref="x", yref="paper",
            text="&#8722;20%", showarrow=False,
            font=dict(size=9, color="#5A6A7A"),
            xanchor="center", yanchor="bottom",
        )
        fig.add_annotation(
            x=upper, y=1.0, xref="x", yref="paper",
            text="+20%", showarrow=False,
            font=dict(size=9, color="#5A6A7A"),
            xanchor="center", yanchor="bottom",
        )

    fig.update_layout(
        height=120,
        margin=dict(l=110, r=50, t=28, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            range=[0, x_max],
            showgrid=True,
            gridcolor="#2D3748",
            gridwidth=1,
            tickprefix="R$ ",
            tickformat=",.0f",
            tickfont=dict(color="#5A6A7A", size=10),
            zeroline=False,
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            tickfont=dict(color="#8899AA", size=11),
        ),
    )
    return fig


# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<h1 style="color: #E2E8F0; font-size: 1.9rem; font-weight: 700; margin: 0 0 6px 0;
           letter-spacing: -0.02em;">
    Alert Review
</h1>
<p style="color: #8899AA; font-size: 0.95rem; margin: 0 0 2rem 0;">
    Classify each flagged transaction. Legitimate resolutions update the cost center baseline.
</p>
""", unsafe_allow_html=True)

# ── Resolution notification ────────────────────────────────────────────────────
if "last_resolution" in st.session_state:
    info = st.session_state.pop("last_resolution")
    if info.get("ok"):
        action = "marked as legitimate &#8212; baseline updated" if info["is_legitimate"] else "confirmed as anomaly"
        accent = "#48BB78" if info["is_legitimate"] else "#E05A5A"
        st.markdown(f"""
        <div style="border: 1px solid {accent}; border-radius: 5px; padding: 11px 16px;
                    margin-bottom: 1.5rem; background: #161B27; color: #E2E8F0; font-size: 13px;">
            <code style="color: {accent}; background: transparent;">{info['txn_id']}</code>
            &ensp;{action}.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="border: 1px solid #E05A5A; border-radius: 5px; padding: 11px 16px;
                    margin-bottom: 1.5rem; background: #161B27; color: #E05A5A; font-size: 13px;">
            Resolution failed: {info.get('error', 'unknown error')}
        </div>
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

alerts = [a for a in data if not a.get("reviewed", 1)]

if not alerts:
    st.markdown("""
    <div style="border: 1px solid #2D3748; border-radius: 5px; padding: 40px; background: #161B27;
                text-align: center;">
        <div style="color: #48BB78; font-size: 14px; font-weight: 600; margin-bottom: 6px;">
            No pending alerts
        </div>
        <div style="color: #5A6A7A; font-size: 13px;">All transactions have been reviewed.</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

count_word = "alert" if len(alerts) == 1 else "alerts"
st.markdown(f"""
<p style="color: #5A6A7A; font-size: 13px; margin-bottom: 1.5rem;">
    {len(alerts)} {count_word} pending review
</p>
""", unsafe_allow_html=True)

# ── Alert cards ────────────────────────────────────────────────────────────────
for alert in alerts:
    txn_id      = alert.get("transaction_id", "")
    cost_center = alert.get("cost_center", "&#8212;")
    amount      = float(alert.get("amount") or 0)
    mean_val    = float(alert.get("mean") or 0)
    deviation   = float(alert.get("deviation") or 0)
    timestamp   = alert.get("timestamp")

    dev_pct   = deviation * 100
    dev_sign  = "+" if dev_pct > 0 else ""
    dev_color = "#E05A5A" if dev_pct > 0 else "#4F8BF9"
    direction = "above mean" if dev_pct > 0 else "below mean"

    try:
        ts_str = datetime.fromtimestamp(float(timestamp)).strftime("%Y-%m-%d %H:%M")
    except Exception:
        ts_str = "&#8212;"

    with st.container(border=True):
        # Cost center + badge
        title_col, badge_col = st.columns([5, 1])
        with title_col:
            st.markdown(f"""
            <div style="color: #E2E8F0; font-size: 1.3rem; font-weight: 700; padding: 2px 0 4px 0;
                        letter-spacing: -0.01em;">
                {cost_center}
            </div>
            """, unsafe_allow_html=True)
        with badge_col:
            st.markdown("""
            <div style="text-align: right; padding-top: 8px;">
                <span style="color: #B7791F; font-size: 11px; font-weight: 600;
                             border: 1px solid #B7791F; border-radius: 3px; padding: 2px 8px;
                             letter-spacing: 0.06em; white-space: nowrap;">
                    FLAGGED
                </span>
            </div>
            """, unsafe_allow_html=True)

        # Amount vs Mean side by side
        amount_col, mean_col = st.columns(2)
        with amount_col:
            st.markdown(f"""
            <div style="padding: 10px 0 6px 0;">
                <div style="color: #5A6A7A; font-size: 11px; text-transform: uppercase;
                            letter-spacing: 0.08em; margin-bottom: 5px;">Transaction Amount</div>
                <div style="color: #E2E8F0; font-size: 1.2rem; font-weight: 700;
                            font-variant-numeric: tabular-nums;">
                    R$ {amount:,.2f}
                </div>
            </div>
            """, unsafe_allow_html=True)
        with mean_col:
            st.markdown(f"""
            <div style="padding: 10px 0 6px 0;">
                <div style="color: #5A6A7A; font-size: 11px; text-transform: uppercase;
                            letter-spacing: 0.08em; margin-bottom: 5px;">Cost Center Mean</div>
                <div style="color: #E2E8F0; font-size: 1.2rem; font-weight: 700;
                            font-variant-numeric: tabular-nums;">
                    R$ {mean_val:,.2f}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Threshold chart
        st.plotly_chart(
            build_threshold_chart(amount, mean_val, dev_pct),
            use_container_width=True,
            config={"displayModeBar": False},
            key=f"chart_{txn_id}",
        )

        # Deviation + Timestamp
        dev_col, ts_col = st.columns(2)
        with dev_col:
            st.markdown(f"""
            <div style="padding: 2px 0 12px 0;">
                <div style="color: #5A6A7A; font-size: 11px; text-transform: uppercase;
                            letter-spacing: 0.08em; margin-bottom: 5px;">Deviation</div>
                <div style="color: {dev_color}; font-size: 1.05rem; font-weight: 700;">
                    {dev_sign}{dev_pct:.1f}%
                    <span style="color: #5A6A7A; font-size: 12px; font-weight: 400;">
                        &ensp;{direction}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with ts_col:
            st.markdown(f"""
            <div style="padding: 2px 0 12px 0;">
                <div style="color: #5A6A7A; font-size: 11px; text-transform: uppercase;
                            letter-spacing: 0.08em; margin-bottom: 5px;">Timestamp</div>
                <div style="color: #8899AA; font-size: 0.95rem; font-weight: 500;
                            font-variant-numeric: tabular-nums;">
                    {ts_str}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Action buttons
        b1, b2, _ = st.columns([2, 2, 5])
        with b1:
            if st.button(
                "Mark as Legitimate",
                key=f"legit_{txn_id}",
                type="primary",
                use_container_width=True,
            ):
                try:
                    resolve_alert(txn_id, is_legitimate=True)
                    st.session_state["last_resolution"] = {
                        "ok": True, "txn_id": txn_id, "is_legitimate": True,
                    }
                except Exception as e:
                    st.session_state["last_resolution"] = {"ok": False, "error": str(e)}
                st.rerun()
        with b2:
            if st.button(
                "Confirm Anomaly",
                key=f"anomaly_{txn_id}",
                use_container_width=True,
            ):
                try:
                    resolve_alert(txn_id, is_legitimate=False)
                    st.session_state["last_resolution"] = {
                        "ok": True, "txn_id": txn_id, "is_legitimate": False,
                    }
                except Exception as e:
                    st.session_state["last_resolution"] = {"ok": False, "error": str(e)}
                st.rerun()
