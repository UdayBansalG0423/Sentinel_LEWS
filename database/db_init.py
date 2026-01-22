import sqlite3

conn = sqlite3.connect("database/local.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS predictions(
    cell_id INTEGER,
    probability REAL,
    timestamp TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS alerts(
    cell_id INTEGER,
    message TEXT,
    sent_time TEXT
)
""")

conn.commit()
conn.close()

print("Database initialized")
