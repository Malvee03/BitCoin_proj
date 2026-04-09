def add_indicators(df):
    df["SMA_7"] = df["price"].rolling(window=7).mean()
    return df