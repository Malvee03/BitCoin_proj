import sqlite3
import pandas as pd

DATABASE_NAME = "bitcoin.db"

# SALVAR DADOS
def save_to_db(df):
    conn = sqlite3.connect(DATABASE_NAME)
    df.to_sql(
        "bitcoin_prices",
        conn,
        if_exists="replace",
        index=False
    )
    conn.close()

# CARREGAR DADOS
def load_from_db():
    conn = sqlite3.connect(DATABASE_NAME)
    df = pd.read_sql(
        "SELECT * FROM bitcoin_prices",
        conn
    )
    conn.close()
    return df