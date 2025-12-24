import sqlite3
import pandas as pd
import os

DB_PATH = "rdp.db"
CSV_FILE = "RDP Master.xlsx - 2025.csv"

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
    if not os.path.exists(DB_PATH) or os.stat(DB_PATH).st_size == 0:
        sync_data()

def sync_data():
    df = pd.read_csv(CSV_FILE)
    # Clean column names
    df.columns = df.columns.str.strip()
    with get_connection() as conn:
        for _, r in df.iterrows():
            conn.execute("""
                INSERT OR REPLACE INTO candidates 
                (candidate_id, name, division, specialty, mentor, 
                 phase_2022, phase_2023, phase_2024, phase_2025, degree, remarks)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(r.get("ID#")), str(r.get("Name ")), str(r.get("Division")), 
                str(r.get("Specialty")), str(r.get("Mentor")),
                str(r.get("Phase in RDP 2022")), str(r.get("Phase in RDP 2023")),
                str(r.get("Phase in RDP 2024")), str(r.get("Phase in RDP 2025")),
                str(r.get("MS/PhD")), str(r.get("IK/OOK COMMENT"))
            ))
        conn.commit()

def clean_val(val):
    if pd.isna(val) or str(val).lower() in ["none", "nan", ""]: return ""
    return str(val).split('.')[0] if '.' in str(val) else str(val)

def get_last_known_phase(row):
    for year in ['phase_2025', 'phase_2024', 'phase_2023', 'phase_2022']:
        val = clean_val(row.get(year))
        if val != "":
            y = year.split('_')[1]
            return f"Phase {val} ({y})"
    return "Not Assigned"

def get_all_candidates(search=None):
    with get_connection() as conn:
        sql = "SELECT * FROM candidates"
        if search:
            sql += f" WHERE name LIKE '%{search}%' OR candidate_id LIKE '%{search}%'"
        return pd.read_sql(sql, conn)
