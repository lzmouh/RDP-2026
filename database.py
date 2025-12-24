import sqlite3
import pandas as pd

DB_PATH = "rdp.db"
MASTER_FILE = "RDP Master.xlsx"

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS candidates (
                candidate_id TEXT PRIMARY KEY,
                name TEXT, division TEXT, specialty TEXT, mentor TEXT,
                phase_2022 TEXT, phase_2023 TEXT, phase_2024 TEXT, phase_2025 TEXT,
                degree TEXT, remarks TEXT
            )
        """)

def clean_val(val):
    if pd.isna(val) or str(val).lower() in ["none", "nan", ""]:
        return ""
    val_str = str(val).strip()
    return val_str.split('.')[0] if '.' in val_str else val_str

def get_last_known_phase(row):
    for year in ['phase_2025', 'phase_2024', 'phase_2023', 'phase_2022']:
        val = clean_val(row.get(year))
        if val != "":
            y_label = year.split('_')[1]
            return f"Phase {val} ({y_label})"
    return "Not Assigned"

def get_all_candidates(search_query=None):
    with get_connection() as conn:
        sql = "SELECT * FROM candidates"
        if search_query:
            sql += f" WHERE name LIKE '%{search_query}%' OR candidate_id LIKE '%{search_query}%' OR mentor LIKE '%{search_query}%'"
        return pd.read_sql(sql, conn)
