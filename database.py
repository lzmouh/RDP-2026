import sqlite3
import pandas as pd
import os

DB_PATH = "rdp.db"
MASTER_FILE = "RDP Master.xlsx"

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    """Initializes tables and auto-loads Excel data if DB is empty."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS candidates (
                candidate_id TEXT PRIMARY KEY,
                name TEXT, division TEXT, specialty TEXT, mentor TEXT,
                phase_2025 TEXT, degree TEXT, nationality TEXT, remarks TEXT,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Placeholder for Scoring/KPI table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS kpis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id TEXT,
                category TEXT,
                score REAL,
                FOREIGN KEY(candidate_id) REFERENCES candidates(candidate_id)
            )
        """)
        
        # Auto-load check
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM candidates")
        if cur.fetchone()[0] == 0 and os.path.exists(MASTER_FILE):
            sync_excel_to_db()

def sync_excel_to_db():
    """Reads Excel and inserts/updates all records."""
    try:
        df = pd.read_excel(MASTER_FILE, engine="openpyxl")
        df.columns = df.columns.str.strip()
        
        with get_connection() as conn:
            for _, r in df.iterrows():
                conn.execute("""
                    INSERT OR REPLACE INTO candidates 
                    (candidate_id, name, division, specialty, mentor, phase_2025, degree, nationality, remarks)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(r.get("ID#")), r.get("Name"), r.get("Division"), 
                    r.get("Specialty"), r.get("Mentor"), r.get("Phase in RDP 2025"),
                    r.get("MS/PhD"), r.get("Nationality"), r.get("Remarks")
                ))
            conn.commit()
    except Exception as e:
        print(f"Sync Error: {e}")

def get_all_candidates(search_query=None):
    with get_connection() as conn:
        if search_query:
            query = "SELECT * FROM candidates WHERE name LIKE ? OR candidate_id LIKE ?"
            return pd.read_sql(query, conn, params=(f"%{search_query}%", f"%{search_query}%"))
        return pd.read_sql("SELECT * FROM candidates", conn)

def update_candidate(data):
    """Saves changes from the UI back to the DB."""
    with get_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO candidates 
            (candidate_id, name, division, specialty, phase_2025, remarks, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, data)
        conn.commit()
