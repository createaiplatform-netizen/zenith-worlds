import sqlite3
from datetime import datetime

class Memory:

    def __init__(self):
        self.conn = sqlite3.connect("trades.db", check_same_thread=False)
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            time TEXT,
            symbol TEXT,
            side TEXT,
            qty INTEGER
        )
        """)

    def log(self, symbol, side, qty):
        self.conn.execute(
            "INSERT INTO trades VALUES (?, ?, ?, ?)",
            (str(datetime.now()), symbol, side, qty)
        )
        self.conn.commit()