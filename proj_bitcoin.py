import streamlit as st
import pandas as pd
import requests
import numpy as np
import time
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from db_bitcoin_proj import save_to_db
from indicadores import add_indicators

# Configuração da página

st.set_page_config(
    page_title="Bitcoin Intelligence Dashboard",
    page_icon="₿",
    layout="wide"
)

st.markdown(
    """
    <style>

    div.modebar {
        top: -45px !important;
        right: 0px !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)
# Estilo da aplicação

st.markdown(
    """
    <style>

    .main {
        background-color: #0E1117;
    }

    div[data-testid="metric-container"] {
        background-color: #161B22;
        border: 1px solid #30363D;
        padding: 15px;
        border-radius: 12px;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# Sidebar

with st.sidebar:

    st.title("⚙️ Configurações")

    days = st.slider(
        "Período analisado",
        30,
        365,
        180
    )

    prediction_days = st.slider(
        "Dias de projeção",
        7,
        30,
        14
    )

# Header

st.title("₿ Bitcoin Intelligence Dashboard")

st.caption(
    "Plataforma analítica para monitoramento do Bitcoin"
)

# API

@st.cache_data(ttl=300)
def get_data(days):

    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"

    params = {
        "vs_currency": "usd",
        "days": days
    }

    for _ in range(3):

        try:

            response = requests.get(
                url,
                params=params,
                timeout=10
            )

            if response.status_code == 429:
                time.sleep(2)
                continue

            if response.status_code != 200:
                continue

            data = response.json()

            if "prices" not in data:
                continue

            df = pd.DataFrame(
                data["prices"],
                columns=["timestamp", "price"]
            )

            df["date"] = pd.to_datetime(
                df["timestamp"],
                unit="ms"
            )

            return df

        except:
            time.sleep(2)

    return pd.DataFrame()

# Carregar dados

with st.spinner("Carregando dados do mercado..."):

    df = get_data(days)

if df.empty:

    st.error("Erro ao carregar dados da API")

    st.stop()

# Banco de dados

save_to_db(df)

# Indicadores

df = add_indicators(df)

# Métricas principais

current_price = df["price"].iloc[-1]

price_change = (
    (
        df["price"].iloc[-1]
        - df["price"].iloc[-2]
    )
    / df["price"].iloc[-2]
) * 100

volatility = df["volatility"].iloc[-1]

rsi = df["RSI"].iloc[-1]

# Market score

market_score = 50

if rsi < 30:
    market_score += 20

elif rsi > 70:
    market_score -= 20

if price_change > 0:
    market_score += 15

else:
    market_score -= 15

market_score = max(
    0,
    min(100, market_score)
)

# Cards

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Preço Atual",
    f"${current_price:,.2f}",
    f"{price_change:.2f}%"
)

col2.metric(
    "RSI",
    f"{rsi:.2f}"
)

col3.metric(
    "Volatilidade",
    f"{volatility:,.2f}"
)

col4.metric(
    "Market Score",
    f"{market_score}/100"
)

# Gráfico principal

st.subheader("📈 Análise Técnica")

fig = make_subplots(
    rows=2,
    cols=1,
    shared_xaxes=True,
    vertical_spacing=0.12,
    row_heights=[0.75, 0.25]
)

# Preço do Bitcoin

fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=df["price"],
        name="Bitcoin",
        line=dict(width=3)
    ),
    row=1,
    col=1
)

# SMA 7

fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=df["SMA_7"],
        name="SMA 7",
        line=dict(
            dash="dash",
            width=2
        )
    ),
    row=1,
    col=1
)

# SMA 30

fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=df["SMA_30"],
        name="SMA 30",
        line=dict(
            dash="dot",
            width=2
        )
    ),
    row=1,
    col=1
)

# RSI

fig.add_trace(
    go.Scatter(
        x=df["date"],
        y=df["RSI"],
        name="RSI",
        line=dict(
            color="#A855F7",
            width=3
        )
    ),
    row=2,
    col=1
)

# Linhas do RSI

fig.add_hline(
    y=70,
    line_dash="dash",
    line_color="red",
    annotation_text="Sobrecompra",
    row=2,
    col=1
)

fig.add_hline(
    y=30,
    line_dash="dash",
    line_color="green",
    annotation_text="Sobrevenda",
    row=2,
    col=1
)

# Áreas coloridas do RSI

fig.add_hrect(
    y0=70,
    y1=100,
    fillcolor="red",
    opacity=0.08,
    line_width=0,
    row=2,
    col=1
)

fig.add_hrect(
    y0=0,
    y1=30,
    fillcolor="green",
    opacity=0.08,
    line_width=0,
    row=2,
    col=1
)

# Layout

fig.update_layout(
    height=800,
    template="plotly_dark",
    hovermode="x unified",
    margin=dict(
        t=50,
        b=40,
        l=40,
        r=40
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    )
)

# Eixos

fig.update_yaxes(
    title_text="Preço USD",
    row=1,
    col=1
)

fig.update_yaxes(
    title_text="RSI",
    range=[0, 100],
    row=2,
    col=1
)

# Exibir gráfico

st.plotly_chart(
    fig,
    use_container_width=True,
    config={
        "displayModeBar": True,
        "scrollZoom": True,
        "displaylogo": False,
        "modeBarButtonsToAdd": [
            "zoom2d",
            "pan2d",
            "resetScale2d",
            "zoomIn2d",
            "zoomOut2d",
            "autoScale2d"
        ]
    }
)

# Tendência de mercado

st.subheader("📊 Tendência de Mercado")

sma = df["SMA_7"].dropna()

if len(sma) > 5:

    slope = sma.iloc[-1] - sma.iloc[-5]

    last_price = df["price"].iloc[-1]

    last_sma = sma.iloc[-1]

    if last_price > last_sma and slope > 0:

        st.success(
            "📈 Mercado em tendência de ALTA"
        )

        signal = "COMPRA"

    elif last_price < last_sma and slope < 0:

        st.error(
            "📉 Mercado em tendência de BAIXA"
        )

        signal = "VENDA"

    else:

        st.warning(
            "➡️ Mercado lateralizado"
        )

        signal = "AGUARDAR"

    st.metric(
        "Sinal Atual",
        signal
    )

# Projeção estatística

st.subheader("🔮 Projeção Estatística")

if len(df) > 10:

    recent_trend = (
        df["price"].iloc[-1]
        - df["price"].iloc[-7]
    ) / 7

    last_price = df["price"].iloc[-1]

    volatility_factor = volatility * 0.12

    predictions = []

    upper_band = []

    lower_band = []

    current_price_projection = last_price

    for _ in range(prediction_days):

        noise = np.random.normal(
            0,
            volatility_factor
        )

        current_price_projection += (
            recent_trend + noise
        )

        predictions.append(
            current_price_projection
        )

        upper_band.append(
            current_price_projection
            + volatility_factor * 2
        )

        lower_band.append(
            current_price_projection
            - volatility_factor * 2
        )

    future_dates = pd.date_range(
        start=df["date"].max(),
        periods=prediction_days + 1,
        freq="D"
    )[1:]

    pred_fig = go.Figure()

    pred_fig.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["price"],
            mode="lines",
            name="Histórico",
            line=dict(width=3)
        )
    )

    pred_fig.add_trace(
        go.Scatter(
            x=future_dates,
            y=predictions,
            mode="lines+markers",
            name="Projeção Estatística",
            line=dict(
                dash="dash",
                width=4
            ),
            marker=dict(size=7)
        )
    )

    pred_fig.add_trace(
        go.Scatter(
            x=future_dates,
            y=upper_band,
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip"
        )
    )

    pred_fig.add_trace(
        go.Scatter(
            x=future_dates,
            y=lower_band,
            fill='tonexty',
            fillcolor='rgba(0,176,246,0.15)',
            line=dict(width=0),
            name='Faixa de Confiança',
            hoverinfo="skip"
        )
    )

    pred_fig.add_hline(
        y=last_price,
        line_dash="dot",
        annotation_text="Preço Atual"
    )

    pred_fig.update_layout(
        template="plotly_dark",
        hovermode="x unified",
        height=550,
        margin=dict(
            t=60,
            b=40,
            l=40,
            r=40
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis_title="Data",
        yaxis_title="Preço USD"
    )

    pred_fig.update_xaxes(
        showgrid=True,
        gridwidth=1
    )

    pred_fig.update_yaxes(
        showgrid=True,
        gridwidth=1
    )

    st.plotly_chart(
        pred_fig,
        use_container_width=True,
        config={
            "displayModeBar": True,
            "scrollZoom": True,
            "displaylogo": False,
            "modeBarButtonsToAdd": [
                "zoom2d",
                "pan2d",
                "resetScale2d",
                "zoomIn2d",
                "zoomOut2d",
                "autoScale2d"
            ]
        }
    )

    projected_change = (
        (
            predictions[-1]
            - last_price
        ) / last_price
    ) * 100

    if projected_change > 3:

        st.success(
            f"📈 Expectativa de alta de {projected_change:.2f}% nos próximos {prediction_days} dias."
        )

    elif projected_change < -3:

        st.error(
            f"📉 Expectativa de queda de {abs(projected_change):.2f}% nos próximos {prediction_days} dias."
        )

    else:

        st.warning(
            "➡️ Mercado projetado em consolidação lateral."
        )

# Botão de atualização

if st.button("🔄 Atualizar Dados"):

    st.cache_data.clear()

    st.rerun()

# Footer

st.markdown("---")

st.caption(
    "Bitcoin Intelligence Dashboard • Projeto Final"
)