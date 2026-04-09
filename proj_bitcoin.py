import streamlit as st
import pandas as pd
import requests
import numpy as np
import time
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression

from db_bitcoin_proj import save_to_db
from indicadores import add_indicators

st.set_page_config(page_title="Dashboard Bitcoin", layout="wide")

st.title("📈 Dashboard Bitcoin")

days = 180

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
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 429:
                time.sleep(2)
                continue

            if response.status_code != 200:
                continue

            data = response.json()

            if "prices" not in data:
                continue

            prices = data["prices"]

            df = pd.DataFrame(prices, columns=["timestamp", "price"])
            df["date"] = pd.to_datetime(df["timestamp"], unit="ms")

            return df

        except:
            time.sleep(2)

    return pd.DataFrame()

df = get_data(days)

if df.empty:
    st.error("Erro ao carregar dados da API")
    st.stop()

save_to_db(df)
df = add_indicators(df)

# PREPARAR DATAS
df["month"] = df["date"].dt.to_period("M")
df["year"] = df["date"].dt.year

current_month = df["month"].max()
previous_month = current_month - 1

current_year = df["year"].max()
previous_year = current_year - 1

# COMPARAÇÃO MENSAL
df_current_month = df[df["month"] == current_month]
df_previous_month = df[df["month"] == previous_month]

avg_current_month = df_current_month["price"].mean()
avg_previous_month = df_previous_month["price"].mean()

delta_month = 0
if avg_previous_month != 0:
    delta_month = ((avg_current_month - avg_previous_month) / avg_previous_month) * 100

st.subheader("📅 Comparação Mensal")

col1, col2 = st.columns(2)

col1.metric("Mês Atual", f"${avg_current_month:,.2f}")
col2.metric("Mês Anterior", f"${avg_previous_month:,.2f}", delta=f"{delta_month:.2f}%")

# COMPARAÇÃO ANUAL
df_current_year = df[df["year"] == current_year]
df_previous_year = df[df["year"] == previous_year]

avg_current_year = df_current_year["price"].mean()
avg_previous_year = df_previous_year["price"].mean()

delta_year = 0
if avg_previous_year != 0:
    delta_year = ((avg_current_year - avg_previous_year) / avg_previous_year) * 100

st.subheader("📊 Comparação Anual")

col3, col4 = st.columns(2)

col3.metric("Ano Atual", f"${avg_current_year:,.2f}")
col4.metric("Ano Anterior", f"${avg_previous_year:,.2f}", delta=f"{delta_year:.2f}%")

# MÉTRICA ATUAL
st.subheader("💰 Preço Atual")
st.metric("Bitcoin (USD)", f"${df['price'].iloc[-1]:,.2f}")

# SLIDER DE VISUALIZAÇÃO
range_days = st.slider(
    "Visualizar últimos dias:",
    7, len(df), 30
)

df_filtered = df.tail(range_days)

# GRÁFICO INTERATIVO
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df_filtered["date"],
    y=df_filtered["price"],
    mode='lines+markers',
    name='Preço',
    line=dict(width=3),
))

fig.add_trace(go.Scatter(
    x=df_filtered["date"],
    y=df_filtered["SMA_7"],
    mode='lines+markers',
    name='Média Móvel (7)',
    line=dict(dash='dash', width=2),
))

fig.update_layout(
    title="📊 Evolução do Bitcoin",
    xaxis_title="Data",
    yaxis_title="Preço USD",
    xaxis=dict(
        tickformat="%d/%m",
        rangeslider=dict(visible=True)
    ),
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)

# TENDÊNCIA CORRETA
st.subheader("📊 Tendência")

sma = df_filtered["SMA_7"].dropna()

if len(sma) > 5:

    # Inclinação da média
    slope = sma.iloc[-1] - sma.iloc[-5]

    # Últimos valores
    last_price = df_filtered["price"].iloc[-1]
    last_sma = sma.iloc[-1]

    # Lógica combinada
    if last_price > last_sma and slope > 0:
        st.markdown("### 🔴 📉 Tendência de BAIXA")
        st.progress(100)

    elif last_price < last_sma and slope < 0:
        st.markdown("### 🟢 📈 Tendência de ALTA")
        st.progress(30)

    else:
        st.markdown("### ⚪ 📊 Tendência LATERAL")
        st.progress(50)

else:
    st.warning("Dados insuficientes para análise de tendência")

# PREVISÃO
if len(df) > 10:

    df["days"] = (df["date"] - df["date"].min()).dt.days

    X = df["days"].values.reshape(-1, 1)
    y = df["price"].values

    model = LinearRegression()
    model.fit(X, y)

    future_days = np.array(range(X[-1][0] + 1, X[-1][0] + 8)).reshape(-1, 1)
    predictions = model.predict(future_days)

    future_dates = pd.date_range(
        start=df["date"].max(),
        periods=8,
        freq="D"
    )[1:]

    fig_pred = go.Figure()

    fig_pred.add_trace(go.Scatter(
        x=df["date"],
        y=df["price"],
        mode='lines',
        name='Histórico'
    ))

    fig_pred.add_trace(go.Scatter(
        x=future_dates,
        y=predictions,
        mode='lines+markers',
        name='Previsão',
        line=dict(dash='dash')
    ))

    fig_pred.update_layout(
        title="🔮 Previsão de Preço",
        xaxis_title="Data",
        yaxis_title="Preço USD",
        xaxis=dict(tickformat="%d/%m"),
        hovermode="x unified"
    )

    st.plotly_chart(fig_pred, use_container_width=True)

# BOTÃO PARA ATUALIZAR
if st.button("Atualizar dados"):
    st.cache_data.clear()
    st.rerun()