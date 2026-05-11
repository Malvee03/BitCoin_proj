import pandas as pd

# =====================================
# ADICIONAR INDICADORES
# =====================================

def add_indicators(df):

    # =========================
    # MÉDIAS MÓVEIS
    # =========================

    df["SMA_7"] = df["price"].rolling(7).mean()

    df["SMA_30"] = df["price"].rolling(30).mean()

    # =========================
    # RSI
    # =========================

    delta = df["price"].diff()

    gain = delta.clip(lower=0)

    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()

    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss

    df["RSI"] = 100 - (100 / (1 + rs))

    # =========================
    # VOLATILIDADE
    # =========================

    df["volatility"] = (
        df["price"]
        .rolling(7)
        .std()
    )

    return df