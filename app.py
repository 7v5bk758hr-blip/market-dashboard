import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from pandas_datareader import data as pdr
from datetime import datetime

# ==================================
# ページ設定
# ==================================

st.set_page_config(
    page_title="市場サマリー",
    layout="wide"
)

st.title("📊 市場サマリー")

# ==================================
# 指標一覧
# ==================================

all_symbols = {
    "S&P500": "^GSPC",
    "NASDAQ100": "^NDX",
    "日経225": "^N225",
    "USDJPY": "JPY=X",
    "VIX": "^VIX",
    "米10年債": "^TNX",
    "SOX": "^SOX",
    "Gold": "GC=F"
}

# ==================================
# 初期値
# ==================================

if "selected_view" not in st.session_state:
    st.session_state.selected_view = "主要指標"

# ==================================
# ボタンエリア
# ==================================

# 1段目
c1, c2, c3, c4, c5, spacer = st.columns([1, 1, 1, 1, 1, 3])

if c1.button("主要指標"):
    st.session_state.selected_view = "主要指標"

if c2.button("USDJPY"):
    st.session_state.selected_view = "USDJPY"

if c3.button("米10年債"):
    st.session_state.selected_view = "米10年債"

if c4.button("VIX"):
    st.session_state.selected_view = "VIX"

if c5.button("逆イールド"):
    st.session_state.selected_view = "逆イールド"


# 2段目
c1, c2, c3, c4, c5, spacer = st.columns([1, 1, 1, 1, 1, 3])

if c1.button("日経225"):
    st.session_state.selected_view = "日経225"

if c2.button("S&P500"):
    st.session_state.selected_view = "S&P500"

if c3.button("NASDAQ100"):
    st.session_state.selected_view = "NASDAQ100"

if c4.button("SOX"):
    st.session_state.selected_view = "SOX"

if c5.button("Gold"):
    st.session_state.selected_view = "Gold"


# 3段目
c1, c2, c3, c4, spacer = st.columns([1, 1, 1, 1, 4])

if c1.button("日経225 vs USDJPY"):
    st.session_state.selected_view = "日経225 vs USDJPY"

if c2.button("NASDAQ100 vs 米10年債"):
    st.session_state.selected_view = "NASDAQ100 vs 米10年債"

if c3.button("SOX vs NASDAQ"):
    st.session_state.selected_view = "SOX vs NASDAQ"

if c4.button("Gold vs VIX"):
    st.session_state.selected_view = "Gold vs VIX"

# ==================================
# 選択状態
# ==================================

selected_view = st.session_state.selected_view
# ==================================
# 選択中の表示
# ==================================

selected_view = st.session_state.selected_view

st.divider()

st.write(f"選択中 : {selected_view}")

# ==================================
# データ取得
# ==================================

@st.cache_data(ttl=3600)
def get_data(ticker):

    try:

        df = yf.download(
            ticker,
            period="1y",
            auto_adjust=True,
            progress=False
        )

        if df.empty:
            return pd.DataFrame()

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        return df

    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def get_yield_curve_data():

    try:

        start = "2000-01-01"
        end = datetime.today()

        dgs10 = pdr.DataReader(
            "DGS10",
            "fred",
            start,
            end
        )

        dgs2 = pdr.DataReader(
            "DGS2",
            "fred",
            start,
            end
        )

        if dgs10.empty or dgs2.empty:
            return None

        df = pd.concat(
            [dgs10, dgs2],
            axis=1
        )

        df.columns = [
            "10Y",
            "2Y"
        ]

        df = df.dropna()

        if df.empty:
            return None

        df["Spread"] = (
            df["10Y"] -
            df["2Y"]
        )

        return df

    except Exception:
        return None


# ==================================
# 主要指標表示
# ==================================

if selected_view == "主要指標":

    st.subheader("主要指標")

    cols = st.columns(4)

    for i, (name, ticker) in enumerate(all_symbols.items()):

        try:

            df = get_data(ticker)

            if len(df) < 2:
                continue

            latest = float(df["Close"].iloc[-1])
            prev = float(df["Close"].iloc[-2])

            daily_pct = ((latest - prev) / prev) * 100

            current_year = pd.Timestamp.today().year

            ytd_data = df[df.index.year == current_year]

            if len(ytd_data) > 0:
                first_price = float(ytd_data["Close"].iloc[0])
                ytd_pct = ((latest - first_price) / first_price) * 100
            else:
                ytd_pct = 0

            with cols[i % 4]:

                st.metric(
                    label=name,
                    value=f"{latest:,.2f}",
                    delta=f"{daily_pct:+.2f}%"
                )

                st.caption(
                    f"YTD : {ytd_pct:+.2f}%"
                )

        except Exception as e:

            with cols[i % 4]:
                st.error(f"{name}取得失敗")


# ==================================
# 単独チャート表示
# ==================================

elif selected_view in all_symbols:

    ticker = all_symbols[selected_view]

    df = get_data(ticker)

    if len(df) < 2:
        st.error("データ取得失敗")
        st.stop()

    latest = float(df["Close"].iloc[-1])
    prev = float(df["Close"].iloc[-2])

    daily_pct = ((latest - prev) / prev) * 100

    current_year = pd.Timestamp.today().year

    ytd_data = df[df.index.year == current_year]

    if len(ytd_data) > 0:
        first_price = float(ytd_data["Close"].iloc[0])
        ytd_pct = ((latest - first_price) / first_price) * 100
    else:
        ytd_pct = 0

    st.subheader(selected_view)

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "現在値",
        f"{latest:,.2f}"
    )

    c2.metric(
        "前日比",
        f"{daily_pct:+.2f}%"
    )

    c3.metric(
        "YTD",
        f"{ytd_pct:+.2f}%"
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["Close"],
            mode="lines",
            name=selected_view
        )
    )

    fig.update_layout(
        title=f"{selected_view}（1年）",
        height=600,
        hovermode="x unified"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# ==================================
# NASDAQ100 vs 米10年債
# ==================================

elif selected_view == "NASDAQ100 vs 米10年債":

    nasdaq = get_data("^NDX")
    tnx = get_data("^TNX")

    st.subheader("NASDAQ100 vs 米10年債")

    fig = make_subplots(
        specs=[[{"secondary_y": True}]]
    )

    fig.add_trace(
        go.Scatter(
            x=nasdaq.index,
            y=nasdaq["Close"],
            mode="lines",
            name="NASDAQ100",
            line=dict(color="blue", width=2)
        ),
        secondary_y=False
    )

    fig.add_trace(
        go.Scatter(
            x=tnx.index,
            y=tnx["Close"],
            mode="lines",
            name="米10年債",
            line=dict(color="red", width=2)
        ),
        secondary_y=True
    )

    fig.update_yaxes(
        title_text="NASDAQ100",
        secondary_y=False
    )

    fig.update_yaxes(
        title_text="米10年債利回り",
        secondary_y=True
    )

    fig.update_layout(
        height=650,
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.info(
        "NASDAQ100が上昇し、米10年債利回りが低下している場合はハイテク株に追い風となる傾向があります。"
    )

# ==================================
# 日経225 vs USDJPY
# ==================================

elif selected_view == "日経225 vs USDJPY":

    nikkei = get_data("^N225")
    usdjpy = get_data("JPY=X")

    st.subheader("日経225 vs USDJPY")

    fig = make_subplots(
        specs=[[{"secondary_y": True}]]
    )

    fig.add_trace(
        go.Scatter(
            x=nikkei.index,
            y=nikkei["Close"],
            mode="lines",
            name="日経225",
            line=dict(
                color="green",
                width=2
            )
        ),
        secondary_y=False
    )

    fig.add_trace(
        go.Scatter(
            x=usdjpy.index,
            y=usdjpy["Close"],
            mode="lines",
            name="USDJPY",
            line=dict(
                color="orange",
                width=2
            )
        ),
        secondary_y=True
    )

    fig.update_yaxes(
        title_text="日経225",
        secondary_y=False
    )

    fig.update_yaxes(
        title_text="USDJPY",
        secondary_y=True
    )

    fig.update_layout(
        height=650,
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.info(
        "円安（USDJPY上昇）は一般的に日本株の追い風になりやすく、日経225との連動性を確認できます。"
    )

# ==================================
# SOX vs NASDAQ100
# ==================================

elif selected_view == "SOX vs NASDAQ":

    sox = get_data("^SOX")
    nasdaq = get_data("^NDX")

    st.subheader("SOX vs NASDAQ100")

    fig = make_subplots(
        specs=[[{"secondary_y": True}]]
    )

    fig.add_trace(
        go.Scatter(
            x=sox.index,
            y=sox["Close"],
            mode="lines",
            name="SOX",
            line=dict(
                color="purple",
                width=2
            )
        ),
        secondary_y=False
    )

    fig.add_trace(
        go.Scatter(
            x=nasdaq.index,
            y=nasdaq["Close"],
            mode="lines",
            name="NASDAQ100",
            line=dict(
                color="blue",
                width=2
            )
        ),
        secondary_y=True
    )

    fig.update_yaxes(
        title_text="SOX",
        secondary_y=False
    )

    fig.update_yaxes(
        title_text="NASDAQ100",
        secondary_y=True
    )

    fig.update_layout(
        height=650,
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.info(
        "SOXがNASDAQ100を上回って推移している場合、半導体セクター主導の強い上昇相場を示すことが多いです。"
    )

# ==================================
# Gold vs VIX
# ==================================

elif selected_view == "Gold vs VIX":

    gold = get_data("GC=F")
    vix = get_data("^VIX")

    st.subheader("Gold vs VIX")

    fig = make_subplots(
        specs=[[{"secondary_y": True}]]
    )

    fig.add_trace(
        go.Scatter(
            x=gold.index,
            y=gold["Close"],
            mode="lines",
            name="Gold",
            line=dict(
                color="gold",
                width=2
            )
        ),
        secondary_y=False
    )

    fig.add_trace(
        go.Scatter(
            x=vix.index,
            y=vix["Close"],
            mode="lines",
            name="VIX",
            line=dict(
                color="red",
                width=2
            )
        ),
        secondary_y=True
    )

    fig.update_yaxes(
        title_text="Gold",
        secondary_y=False
    )

    fig.update_yaxes(
        title_text="VIX",
        secondary_y=True
    )

    fig.update_layout(
        height=650,
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.info(
        "GoldとVIXが同時上昇する場合はリスクオフ傾向、VIX低下とGold横ばい・下落はリスクオン傾向として参考になります。"
    )


# ==================================
# 米国逆イールド
# ==================================
elif selected_view == "逆イールド":

    st.subheader("📉 米国逆イールド")

    df = get_yield_curve_data()

    if df is None:
        st.error("逆イールドデータ取得失敗")
        st.stop()

    current_10y = float(df["10Y"].iloc[-1])
    current_2y = float(df["2Y"].iloc[-1])
    current_spread = float(df["Spread"].iloc[-1])

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "米10年債",
        f"{current_10y:.2f}%"
    )

    c2.metric(
        "米2年債",
        f"{current_2y:.2f}%"
    )

    c3.metric(
        "スプレッド",
        f"{current_spread:.2f}%"
    )

    if current_spread > 0.5:
        st.success(
            f"🟢 正常（{current_spread:.2f}%）"
        )

    elif current_spread > 0:
        st.warning(
            f"🟡 フラット化注意（{current_spread:.2f}%）"
        )

    else:
        st.error(
            f"🔴 逆イールド発生中（{current_spread:.2f}%）"
        )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["Spread"],
            mode="lines",
            name="10年債−2年債"
        )
    )

    fig.add_hline(
        y=0,
        line_color="red",
        line_dash="dash",
        annotation_text="逆イールドライン"
    )

    fig.update_layout(
        title="米国10年債−2年債スプレッド",
        height=650,
        hovermode="x unified"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )
