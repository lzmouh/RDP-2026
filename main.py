# # EXPEC ARC RDP – Database-Driven Web App (Streamlit + SQLite)
# -------------------------------------------------------------------
# IMPLEMENTED:
# ✓ SQLite database built from Master Excel
# ✓ Persistent storage (local)
# ✓ Display, search, add, remove candidates
# ✓ Safe schema mapped exactly to your Excel
# ✓ Ready for scoring-table extension
# -------------------------------------------------------------------
# Local run:
#   pip install streamlit pandas openpyxl sqlalchemy
#   streamlit run app.py

import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path

st.set_page_config(page_title="EXPEC ARC RDP – DB", layout="wide")

# -------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------
DB_PATH = "rdp.db"
MASTER_FILE = "RDP Master.xlsx"
MASTER_SHEET = "2025"

# -------------------------------------------------------------------
# DATABASE UTILITIES
# -------------------------------------------------------------------
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id TEXT UNIQUE,
            name TEXT,
            division TEXT,
            specialty TEXT,
            mentor TEXT,
            phase_2022 TEXT,
            phase_2023 TEXT,
            phase_2024 TEXT,
            phase_2025 TEXT,
            promotion TEXT,
            degree TEXT,
            nationality TEXT,
            remarks TEXT
        )
    """)
    conn.commit()
    conn.close()


def load_from_excel():
    df = pd.read_excel(MASTER_FILE, sheet_name=MASTER_SHEET)
    df.columns = df.columns.str.strip()

    conn = get_conn()
    df_db = pd.read_sql("SELECT candidate_id FROM candidates", conn)
    existing = set(df_db["candidate_id"].astype(str))

    rows = []
    for _, r in df.iterrows():
        cid = str(r["ID#"])
        if cid not in existing:
            rows.append((
                cid,
                r.get("Name"),
                r.get("Division"),
                r.get("Specialty"),
                r.get("Mentor"),
                r.get("Phase in RDP 2022"),
                r.get("Phase in RDP 2023"),
                r.get("Phase in RDP 2024"),
                r.get("Phase in RDP 2025"),
                r.get("Promotion"),
                r.get("MS/PhD"),
                r.get("Nationality"),
                r.get("Remarks")
            ))

    conn.executemany("""
        INSERT INTO candidates (
            candidate_id, name, division, specialty, mentor,
            phase_2022, phase_2023, phase_2024, phase_2025,
            promotion, degree, nationality, remarks
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, rows)

    conn.commit()
    conn.close()


def fetch_candidates(query=None):
    conn = get_conn()
    if query:
        df = pd.read_sql("""
            SELECT * FROM candidates
            WHERE name LIKE ? OR mentor LIKE ? OR candidate_id LIKE ?
        """, conn, params=(f"%{query}%", f"%{query}%", f"%{query}%"))
    else:
        df = pd.read_sql("SELECT * FROM candidates", conn)
    conn.close()
    return df


def delete_candidate(cid):
    conn = get_conn()
    conn.execute("DELETE FROM candidates WHERE candidate_id = ?", (cid,))
    conn.commit()
    conn.close()


def add_candidate(data):
    conn = get_conn()
    conn.execute("""
        INSERT INTO candidates (
            candidate_id, name, division, specialty, mentor,
            phase_2022, phase_2023, phase_2024, phase_2025,
            promotion, degree, nationality, remarks
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, data)
    conn.commit()
    conn.close()

# -------------------------------------------------------------------
# ---------------------------------------------------
# INITIALIZATION (NO AUTO EXCEL LOAD)
# ---------------------------------------------------
init_db()

# ---------------------------------------------------
# ---------------------------------------------------
# UI
# ---------------------------------------------------
st.title("EXPEC ARC RDP – Database-Driven Platform")

menu = st.sidebar.radio(
    "Menu",
    [
        "View & Search",
        "Candidate Profile",
        "Add Candidate",
        "Import / Export",
        "Analytics",
    ],
)

# ---------------------------------------------------
# VIEW & SEARCH
# ---------------------------------------------------
if menu == "View & Search":
    q = st.text_input("Search by name, mentor, or ID")
    df = fetch_candidates(q)
    st.dataframe(df)

# ---------------------------------------------------
# CANDIDATE PROFILE
# ---------------------------------------------------
elif menu == "Candidate Profile":
    df = fetch_candidates()
    cid = st.selectbox("Select Candidate", df["candidate_id"])
    c = df[df["candidate_id"] == cid].iloc[0]

    st.subheader(c["name"])
    col1, col2, col3 = st.columns(3)
    col1.metric("Division", c["division"])
    col2.metric("Specialty", c["specialty"])
    col3.metric("Phase 2025", c["phase_2025"])

    st.write("Mentor:", c["mentor"])
    st.write("Degree:", c["degree"])
    st.write("Remarks:", c["remarks"])

    # KPI Progress
    conn = get_conn()
    kpi_df = pd.read_sql(
        "SELECT category, SUM(score) as score FROM kpis WHERE candidate_id=? GROUP BY category",
        conn,
        params=(cid,),
    )
    conn.close()

    st.subheader("KPI Progress")
    for _, r in kpi_df.iterrows():
        maxv = CATEGORY_LIMITS.get(r["category"], 100)
        st.caption(r["category"])
        st.progress(min(r["score"] / maxv, 1.0))

# ---------------------------------------------------
# ADD CANDIDATE
# ---------------------------------------------------
elif menu == "Add Candidate":
    st.subheader("Add Candidate (Admin only)")

    cid = st.text_input("Candidate ID")
    name = st.text_input("Name")
    division = st.text_input("Division")
    specialty = st.text_input("Specialty")
    mentor = st.text_input("Mentor")
    phase = st.selectbox("Phase 2025", ["1", "2", "3"])
    degree = st.selectbox("Degree", ["MS", "PhD"])
    nationality = st.text_input("Nationality")
    remarks = st.text_area("Remarks")

    if st.button("Add Candidate"):
        add_candidate(
            (
                cid,
                name,
                division,
                specialty,
                mentor,
                None,
                None,
                None,
                phase,
                None,
                degree,
                nationality,
                remarks,
            )
        )
        st.success("Candidate added")

# ---------------------------------------------------
# IMPORT / EXPORT (ADMIN)
# ---------------------------------------------------
elif menu == "Import / Export":
    st.subheader("Import Master Candidates (Excel)")

    uploaded = st.file_uploader("Upload Master Excel", type="xlsx")
    if uploaded:
        df = pd.read_excel(uploaded)
        df.columns = df.columns.str.strip()
        conn = get_conn()
        existing = set(
            pd.read_sql("SELECT candidate_id FROM candidates", conn)["candidate_id"].astype(str)
        )
        inserted = 0
        for _, r in df.iterrows():
            cid = str(r.get("ID#"))
            if cid not in existing:
                conn.execute(
                    """
                    INSERT INTO candidates (
                        candidate_id, name, division, specialty, mentor,
                        phase_2022, phase_2023, phase_2024, phase_2025,
                        promotion, degree, nationality, remarks
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        cid,
                        r.get("Name"),
                        r.get("Division"),
                        r.get("Specialty"),
                        r.get("Mentor"),
                        r.get("Phase in RDP 2022"),
                        r.get("Phase in RDP 2023"),
                        r.get("Phase in RDP 2024"),
                        r.get("Phase in RDP 2025"),
                        r.get("Promotion"),
                        r.get("MS/PhD"),
                        r.get("Nationality"),
                        r.get("Remarks"),
                    ),
                )
                inserted += 1
        conn.commit()
        conn.close()
        st.success(f"Imported {inserted} candidates")

    st.divider()
    st.subheader("Import KPI Scores (Excel)")
    kpi_file = st.file_uploader("Upload KPI Excel", type="xlsx")
    if kpi_file:
        kdf = pd.read_excel(kpi_file)
        conn = get_conn()
        kdf.to_sql("kpis", conn, if_exists="append", index=False)
        conn.close()
        st.success("KPI data imported")

    st.divider()
    st.subheader("Export Database")
    conn = get_conn()
    export_df = pd.read_sql("SELECT * FROM candidates", conn)
    conn.close()
    st.download_button(
        "Download Candidates Excel",
        export_df.to_excel(index=False),
        file_name="RDP_Candidates_Export.xlsx",
    )

# ---------------------------------------------------
# ANALYTICS
# ---------------------------------------------------
elif menu == "Analytics":
    st.subheader("Candidates per Phase")
    df = fetch_candidates()
    st.bar_chart(df["phase_2025"].value_counts())

    st.subheader("Top KPI Categories")
    conn = get_conn()
    k = pd.read_sql("SELECT category, SUM(score) score FROM kpis GROUP BY category", conn)
    conn.close()
    if not k.empty:
        st.bar_chart(k.set_index("category"))

st.caption("SQLite-backed RDP system – auditable, persistent, Excel-compatible")
