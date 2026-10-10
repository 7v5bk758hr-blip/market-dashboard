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
        "景気モニター",
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

elif category == "景気モニター":

    selected_view = "景気モニター"

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

@st.cache_data(ttl=3600)
def get_sahm_rule_data():

    try:

        start = "2000-01-01"
        end = datetime.today()

        df = pdr.DataReader(
            "SAHMREALTIME",
            "fred",
            start,
            end
        )

        return df.dropna()

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
        return "color: red"

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
        dragmode=False,
        xaxis_tickformat="%Y.%m"
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config=PLOT_CONFIG
    )


# ==================================
# 景気モニター
# ==================================
elif selected_view == "景気モニター":

    st.subheader("📉 景気モニター")

    yc = get_yield_curve_data()

    if yc is None:
        st.error("景気指標取得失敗")
        st.stop()

    spread = float(yc["Spread"].iloc[-1])

    if spread < 0:
        yc_status = "🔴 景気後退警戒"
    elif spread < 0.5:
        yc_status = "🟡 注意"
    else:
        yc_status = "🟢 正常"



    # サームルール
    sahm_df = get_sahm_rule_data()

    latest_sahm = float(
        sahm_df.iloc[-1, 0]
    )

    if latest_sahm >= 0.5:
        sahm_status = "🔴 景気後退"

    elif latest_sahm >= 0.3:
        sahm_status = "🟡 注意"

    else:
        sahm_status = "🟢 正常"



    monitor_data = [
        {
            "指標": "イールドカーブ",
            "現在値": f"{spread:.2f}%",
            "状態": yc_status,
            "景気後退シグナル": "0%未満"
        },
        {
            "指標": "サームルール",
            "現在値": f"{latest_sahm:.2f}",
            "状態": sahm_status,
            "景気後退シグナル": "0.5以上"
        },
    ]


    monitor_df = pd.DataFrame(monitor_data)

    st.dataframe(
        monitor_df,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    st.markdown("### イールドカーブ（10年債－2年債スプレッド）")

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=yc.index,
            y=yc["Spread"],
            mode="lines",
            name="10年債－2年債",
            line=dict(
                color="blue",
                width=2
            )
        )
    )

    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="red"
    )

    fig.update_layout(
        height=400,
        hovermode="x unified",
        dragmode=False,
        xaxis_tickformat="%Y.%m",
        yaxis_title="Spread (%)"
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config=PLOT_CONFIG
    )

    st.divider()

    st.markdown("### サームルール")

    sahm_df = get_sahm_rule_data()

    if sahm_df is not None:

        latest_sahm = float(
            sahm_df.iloc[-1, 0]
        )

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=sahm_df.index,
                y=sahm_df.iloc[:, 0],
                mode="lines",
                name="Sahm Rule",
                line=dict(
                    color="purple",
                    width=2
                )
            )
        )

        fig.add_hline(
            y=0.5,
            line_dash="dash",
            line_color="red"
        )

        fig.update_layout(
            height=400,
            hovermode="x unified",
            dragmode=False,
            xaxis_tickformat="%Y.%m",
            yaxis_title="Sahm Rule"
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config=PLOT_CONFIG
        )

        if latest_sahm >= 0.5:
            st.error(
                f"🔴 景気後退シグナル発生中 : {latest_sahm:.2f}"
            )
        else:
            st.success(
                f"🟢 正常圏 : {latest_sahm:.2f}"
            )

    else:
        st.warning("サームルール取得失敗")


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
            xaxis_tickformat="%Y.%m",
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
            xaxis_tickformat="%Y.%m",
            yaxis_title="Spread (%)"
        )

        st.plotly_chart(
            fig2,
            use_container_width=True,
            config=PLOT_CONFIG
        )

    except Exception as e:

        st.error(f"逆イールド取得失敗: {e}")
