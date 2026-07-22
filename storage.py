import sqlite3
import json

DB_PATH = "crypto_history.db"


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS prices
           (timestamp TEXT, coin TEXT, price REAL, change REAL, data TEXT)"""
    )
    return conn


def save_price(data):
    if "error" in data:
        return
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO prices VALUES (?,?,?,?,?)",
            (data["timestamp"], data["symbol"], data["price"], data["change_24h"], json.dumps(data)),
        )


def get_history(coin="SOL", limit=10):
    with _get_conn() as conn:
        cur = conn.execute(
            "SELECT * FROM prices WHERE coin=? ORDER BY timestamp DESC LIMIT ?", (coin, limit)
        )
        return cur.fetchall()
