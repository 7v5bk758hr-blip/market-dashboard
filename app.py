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

st.divider()

category = st.selectbox(
    "表示カテゴリ",
    [
        "主要指標",
        "株式",
        "為替・金利",
        "相関分析",
        "逆イールド"
    ]
)

selected_view = None

if category == "主要指標":

    selected_view = st.selectbox(
        "主要指標チャート",
        [
            "表示しない",
            "S&P500",
            "NASDAQ100",
            "日経225",
            "USDJPY",
            "VIX",
            "米10年債",
            "SOX",
            "Gold"
        ]
    )

elif category == "株式":

    selected_view = st.selectbox(
        "チャート選択",
        [
            "日経225",
            "S&P500",
            "NASDAQ100",
            "SOX"
        ]
    )

elif category == "為替・金利":

    selected_view = st.selectbox(
        "チャート選択",
        [
            "USDJPY",
            "米10年債",
            "VIX",
            "Gold"
        ]
    )

elif category == "相関分析":

    selected_view = st.selectbox(
        "チャート選択",
        [
            "日経225 vs USDJPY",
            "NASDAQ100 vs 米10年債",
            "SOX vs NASDAQ",
            "Gold vs VIX"
        ]
    )

elif category == "逆イールド":

    selected_view = "逆イールド"
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
# Plotly共通設定
# ==================================

PLOT_CONFIG = {
    "scrollZoom": False,
    "displaylogo": False,
    "modeBarButtonsToRemove": [
        "select2d",
        "lasso2d"
    ]
}

# ==================================
# 色付け
# ==================================
def color_change(val):

    val = str(val)

    if val.startswith("+"):
        return "color: green"

    elif val.startswith("-"):
        return "color: red; font-weight: bold"

    return ""
    
# ==================================
# 主要指標表示
# ==================================
if category == "主要指標":

    # ----------------------
    # 株式
    # ----------------------
    st.subheader("📈 株式")

    stock_symbols = {
        "S&P500": "^GSPC",
        "NASDAQ100": "^NDX",
        "日経225": "^N225",
        "SOX": "^SOX",
        "Gold": "GC=F"
    }

    stock_data = []

    for name, ticker in stock_symbols.items():

        try:
            df = get_data(ticker)

            if len(df) < 2:
                continue

            latest = float(df["Close"].iloc[-1])
            prev = float(df["Close"].iloc[-2])

            daily_pct = ((latest - prev) / prev) * 100

            if len(df) >= 22:
                month_price = float(df["Close"].iloc[-22])
                monthly_pct = ((latest - month_price) / month_price) * 100
            else:
                monthly_pct = 0

            current_year = pd.Timestamp.today().year
            ytd_data = df[df.index.year == current_year]

            if len(ytd_data) > 0:
                first_price = float(ytd_data["Close"].iloc[0])
                ytd_pct = ((latest - first_price) / first_price) * 100
            else:
                ytd_pct = 0

            stock_data.append({
                "名称": name,
                "現在値": f"{latest:,.0f}",
                "前日比": f"{daily_pct:+.2f}%",
                "前月比": f"{monthly_pct:+.2f}%",
                "年初来": f"{ytd_pct:+.2f}%"
            })

        except Exception:
            pass

    stock_df = pd.DataFrame(stock_data)

    st.dataframe(
        stock_df.style.map(
            color_change,
            subset=["前日比", "前月比", "年初来"]
        ),
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # ----------------------
    # 為替・金利
    # ----------------------
    st.subheader("💱 為替・金利")

    macro_symbols = {
        "USDJPY": "JPY=X",
        "米10年債": "^TNX",
        "VIX": "^VIX"
    }

    macro_data = []

    for name, ticker in macro_symbols.items():

        try:
            df = get_data(ticker)

            if len(df) < 2:
                continue

            latest = float(df["Close"].iloc[-1])
            prev = float(df["Close"].iloc[-2])

            daily_pct = ((latest - prev) / prev) * 100

            if len(df) >= 22:
                month_price = float(df["Close"].iloc[-22])
                monthly_pct = ((latest - month_price) / month_price) * 100
            else:
                monthly_pct = 0

            current_year = pd.Timestamp.today().year
            ytd_data = df[df.index.year == current_year]

            if len(ytd_data) > 0:
                first_price = float(ytd_data["Close"].iloc[0])
                ytd_pct = ((latest - first_price) / first_price) * 100
            else:
                ytd_pct = 0

            macro_data.append({
                "名称": name,
                "現在値": f"{latest:,.2f}",
                "前日比": f"{daily_pct:+.2f}%",
                "前月比": f"{monthly_pct:+.2f}%",
                "年初来": f"{ytd_pct:+.2f}%"
            })

        except Exception:
            pass

    macro_df = pd.DataFrame(macro_data)

    st.dataframe(
        macro_df.style.map(
            color_change,
            subset=["前日比", "前月比", "年初来"]
        ),
        use_container_width=True,
        hide_index=True
    )
# ==================================
# 単独チャート表示
# ==================================

if selected_view != "表示しない" and selected_view in all_symbols:

    ticker = all_symbols[selected_view]

    df = get_data(ticker)

    if len(df) < 2:
        st.error("データ取得失敗")
        st.stop()

    latest = float(df["Close"].iloc[-1])
    prev = float(df["Close"].iloc[-2])

    # 前日比
    daily_pct = ((latest - prev) / prev) * 100

    # 前月比（約22営業日）
    if len(df) >= 22:
        month_price = float(df["Close"].iloc[-22])
        monthly_pct = ((latest - month_price) / month_price) * 100
    else:
        monthly_pct = 0

    # 年初来
    current_year = pd.Timestamp.today().year

    ytd_data = df[df.index.year == current_year]

    if len(ytd_data) > 0:
        first_price = float(ytd_data["Close"].iloc[0])
        ytd_pct = ((latest - first_price) / first_price) * 100
    else:
        ytd_pct = 0

    st.subheader(selected_view)

    summary_df = pd.DataFrame([
        {
            "現在値": f"{latest:,.2f}",
            "前日比": f"{daily_pct:+.2f}%",
            "前月比": f"{monthly_pct:+.2f}%",
            "年初来": f"{ytd_pct:+.2f}%"
        }
    ])

    st.dataframe(
        summary_df.style.map(
            color_change,
            subset=["前日比", "前月比", "年初来"]
        ),
        use_container_width=True,
        hide_index=True
    )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["Close"],
            mode="lines",
            name=selected_view,
            line=dict(width=2)
        )
    )

    fig.update_layout(
        title=f"{selected_view}（1年）",
        height=400,
        hovermode="x unified",
        dragmode=False
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config=PLOT_CONFIG
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
        height=400,
        hovermode="x unified",
        dragmode=False,
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
        use_container_width=True,
        config=PLOT_CONFIG
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
        height=400,
        hovermode="x unified",
        dragmode=False,
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
        use_container_width=True,
        config=PLOT_CONFIG
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
        height=400,
        hovermode="x unified",
        dragmode=False,
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
        use_container_width=True,
        config=PLOT_CONFIG
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
        height=400,
        hovermode="x unified",
        dragmode=False,
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
        use_container_width=True,
        config=PLOT_CONFIG
    )

    st.info(
        "GoldとVIXが同時上昇する場合はリスクオフ傾向、VIX低下とGold横ばい・下落はリスクオン傾向として参考になります。"
    )


# ==================================
# 逆イールド（10年債 - 2年債）
# ==================================
elif selected_view == "逆イールド":

    st.subheader("🇺🇸 米国債 イールドカーブ")

    try:

        df = get_yield_curve_data()

        if df is None:
            st.error("逆イールドデータ取得失敗")
            st.stop()

        latest = float(df["Spread"].iloc[-1])

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "米10年債",
            f"{df['10Y'].iloc[-1]:.2f}%"
        )

        c2.metric(
            "米2年債",
            f"{df['2Y'].iloc[-1]:.2f}%"
        )

        c3.metric(
            "スプレッド",
            f"{latest:.2f}%"
        )

        if latest < 0:
            st.error(f"🔴 逆イールド継続中 : {latest:.2f}%")

        elif latest < 0.5:
            st.warning(f"🟡 フラット化注意 : {latest:.2f}%")

        else:
            st.success(f"🟢 正常なイールドカーブ : {latest:.2f}%")

        # -------------------------
        # 上段：10年債 vs 2年債
        # -------------------------

        fig1 = go.Figure()

        fig1.add_trace(
            go.Scatter(
                x=df.index,
                y=df["10Y"],
                mode="lines",
                name="米10年債",
                line=dict(
                    color="blue",
                    width=2
                )
            )
        )

        fig1.add_trace(
            go.Scatter(
                x=df.index,
                y=df["2Y"],
                mode="lines",
                name="米2年債",
                line=dict(
                    color="red",
                    width=2
                )
            )
        )

        fig1.update_layout(
            title="米10年債 vs 米2年債",
            height=400,
            hovermode="x unified",
            dragmode=False,
            yaxis_title="利回り (%)",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        st.plotly_chart(
            fig1,
            use_container_width=True,
            config=PLOT_CONFIG
        )

        # -------------------------
        # 下段：スプレッド
        # -------------------------

        fig2 = go.Figure()

        fig2.add_trace(
            go.Scatter(
                x=df.index,
                y=df["Spread"],
                mode="lines",
                name="10年債−2年債",
                line=dict(
                    color="green",
                    width=2
                )
            )
        )

        fig2.add_hline(
            y=0,
            line_dash="dash",
            line_color="red"
        )

        fig2.update_layout(
            title="10年債−2年債スプレッド",
            height=400,
            hovermode="x unified",
            dragmode=False,
            yaxis_title="Spread (%)"
        )

        st.plotly_chart(
            fig2,
            use_container_width=True,
            config=PLOT_CONFIG
        )

    except Exception as e:

        st.error(f"逆イールド取得失敗: {e}")
