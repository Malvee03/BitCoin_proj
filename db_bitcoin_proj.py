import sqlite3
import pandas as pd

def save_to_db(df):
    conn = sqlite3.connect("bitcoin.db")
    df.to_sql("prices", conn, if_exists="replace", index=False)
    conn.close()

def load_from_db():
    conn = sqlite3.connect("bitcoin.db")
    df = pd.read_sql("SELECT * FROM prices", conn)
    conn.close()
    return df