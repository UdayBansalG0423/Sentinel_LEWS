import sqlite3

DB = "database/local.db"

def save_prediction(cell_id, prob, ts):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("INSERT INTO predictions VALUES (?,?,?)",(cell_id,prob,ts))
    conn.commit()
    conn.close()
