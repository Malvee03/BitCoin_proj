import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression
import time

st.set_page_config(page_title="Dashboard Bitcoin", layout="wide")

st.title("📈 Dashboard Bitcoin")

# -----------------------------
# FILTRO DE PERÍODO
# -----------------------------
days = st.selectbox("Escolha o período:", [7, 30, 90, 180])

# -----------------------------
# CACHE (EVITA RATE LIMIT)
# -----------------------------
@st.cache_data(ttl=300)  # 5 minutos
def get_data(days):
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
    params = {
        "vs_currency": "usd",
        "days": days
    }

    for attempt in range(3):  # tenta até 3 vezes
        try:
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 429:
                time.sleep(2)  # espera se tomou rate limit
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

        except requests.exceptions.RequestException:
            time.sleep(2)

    return pd.DataFrame()

# -----------------------------
# CARREGAR DADOS
# -----------------------------
df = get_data(days)

if df.empty:
    st.error("⚠️ Não foi possível carregar os dados. Tente novamente em alguns segundos.")
    st.stop()

# -----------------------------
# TÍTULO DINÂMICO
# -----------------------------
st.subheader(f"Preço do Bitcoin (últimos {days} dias)")

# -----------------------------
# MÉTRICA (PREÇO ATUAL)
# -----------------------------
st.metric("Preço atual do Bitcoin (USD)", f"${df['price'].iloc[-1]:,.2f}")

# -----------------------------
# GRÁFICO HISTÓRICO
# -----------------------------
fig, ax = plt.subplots()
ax.plot(df["date"], df["price"])
ax.set_xlabel("Data")
ax.set_ylabel("Preço USD")

st.pyplot(fig)

# -----------------------------
# PREVISÃO (REGRESSÃO LINEAR)
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

    # -----------------------------
    # GRÁFICO COM PREVISÃO
    # -----------------------------
    fig, ax = plt.subplots()
    ax.plot(df["date"], df["price"], label="Histórico")
    ax.plot(future_dates, predictions, linestyle="dashed", label="Previsão")

    ax.set_xlabel("Data")
    ax.set_ylabel("Preço USD")
    ax.legend()

    st.pyplot(fig)

else:
    st.warning("Poucos dados para gerar previsão")

# -----------------------------
# BOTÃO DE ATUALIZAÇÃO
# -----------------------------
if st.button("🔄 Atualizar dados"):
    st.cache_data.clear()
    st.rerun()