import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression
import time

# IMPORTS AJUSTADOS
from db_bitcoin_proj import save_to_db
from indicadores import add_indicators

st.set_page_config(page_title="Dashboard Bitcoin", layout="wide")

st.title("📈 Dashboard Bitcoin")

# -----------------------------
# FILTRO
# -----------------------------
days = st.selectbox("Escolha o período:", [7, 30, 90, 180])

# -----------------------------
# API COM CACHE
# -----------------------------
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

# -----------------------------
# CARREGAR DADOS
# -----------------------------
df = get_data(days)

if df.empty:
    st.error("Erro ao carregar dados da API")
    st.stop()

# -----------------------------
# SALVAR NO BANCO
# -----------------------------
save_to_db(df)

# -----------------------------
# INDICADORES
# -----------------------------
df = add_indicators(df)

# -----------------------------
# TÍTULO
# -----------------------------
st.subheader(f"Preço do Bitcoin (últimos {days} dias)")

# -----------------------------
# MÉTRICA
# -----------------------------
st.metric("Preço atual (USD)", f"${df['price'].iloc[-1]:,.2f}")

# -----------------------------
# GRÁFICO COM MÉDIA MÓVEL
# -----------------------------
fig, ax = plt.subplots()
ax.plot(df["date"], df["price"], label="Preço")
ax.plot(df["date"], df["SMA_7"], label="Média móvel (7 dias)")

ax.set_xlabel("Data")
ax.set_ylabel("Preço USD")
ax.legend()

st.pyplot(fig)

# -----------------------------
# TENDÊNCIA
# -----------------------------
if df["price"].iloc[-1] > df["SMA_7"].iloc[-1]:
    st.success("📈 Tendência de ALTA")
else:
    st.error("📉 Tendência de BAIXA")

# -----------------------------
# PREVISÃO
# -----------------------------
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

    fig, ax = plt.subplots()
    ax.plot(df["date"], df["price"], label="Histórico")
    ax.plot(future_dates, predictions, linestyle="dashed", label="Previsão")

    ax.legend()
    st.pyplot(fig)

# -----------------------------
# BOTÃO ATUALIZAR
# -----------------------------
if st.button("🔄 Atualizar dados"):
    st.cache_data.clear()
    st.rerun()