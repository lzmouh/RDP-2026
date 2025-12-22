This rewritten version cleans up the logic, fixes the `openpyxl` export buffer issue, ensures the `kpis` table exists to prevent crashes, and adds the missing `CATEGORY_LIMITS` variable.

I have also streamlined the database connections to be more "Pythonic" using context managers (`with` statements).

```python
import streamlit as st
import pandas as pd
import sqlite3
import io
from pathlib import Path

# -------------------------------------------------------------------
# CONFIG & SETTINGS
# -------------------------------------------------------------------
st.set_page_config(page_title="EXPEC ARC RDP – DB", layout="wide")

DB_PATH = "rdp.db"
# Define limits for KPI progress bars (Missing in original snippet)
CATEGORY_LIMITS = {
    "Technical": 100,
    "Leadership": 100,
    "Soft Skills": 100,
    "Research": 100
}

# -------------------------------------------------------------------
# DATABASE UTILITIES
# -------------------------------------------------------------------
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    with get_conn() as conn:
        cursor = conn.cursor()
        # Candidates Table
        cursor.execute("""
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
        # KPI Table (Crucial to prevent "no such table" errors)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kpis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id TEXT,
                category TEXT,
                score REAL,
                FOREIGN KEY(candidate_id) REFERENCES candidates(candidate_id)
            )
        """)
        conn.commit()

def fetch_candidates(query=None):
    with get_conn() as conn:
        if query:
            sql = """SELECT * FROM candidates 
                     WHERE name LIKE ? OR mentor LIKE ? OR candidate_id LIKE ?"""
            return pd.read_sql(sql, conn, params=(f"%{query}%", f"%{query}%", f"%{query}%"))
        return pd.read_sql("SELECT * FROM candidates", conn)

def add_candidate(data):
    try:
        with get_conn() as conn:
            conn.execute("""
                INSERT INTO candidates (
                    candidate_id, name, division, specialty, mentor,
                    phase_2022, phase_2023, phase_2024, phase_2025,
                    promotion, degree, nationality, remarks
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, data)
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        st.error("Error: Candidate ID already exists.")
        return False

# -------------------------------------------------------------------
# INITIALIZATION
# -------------------------------------------------------------------
init_db()

# -------------------------------------------------------------------
# UI / SIDEBAR NAVIGATION
# -------------------------------------------------------------------
st.title("EXPEC ARC RDP – Database-Driven Platform")

menu = st.sidebar.radio(
    "Menu",
    ["View & Search", "Candidate Profile", "Add Candidate", "Import / Export", "Analytics"]
)

# ---------------------------------------------------
# VIEW & SEARCH
# ---------------------------------------------------
if menu == "View & Search":
    st.subheader("Candidate Directory")
    q = st.text_input("Search by name, mentor, or ID")
    df = fetch_candidates(q)
    st.dataframe(df, use_container_width=True)

# ---------------------------------------------------
# CANDIDATE PROFILE
# ---------------------------------------------------
elif menu == "Candidate Profile":
    st.subheader("Detailed Candidate View")
    all_cands = fetch_candidates()
    
    if all_cands.empty:
        st.info("No candidates found in database.")
    else:
        cid = st.selectbox("Select Candidate ID", all_cands["candidate_id"])
        c = all_cands[all_cands["candidate_id"] == cid].iloc[0]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Name", c["name"])
            st.write(f"**Division:** {c['division']}")
        with col2:
            st.metric("Phase 2025", c["phase_2025"])
            st.write(f"**Specialty:** {c['specialty']}")
        with col3:
            st.metric("Degree", c["degree"])
            st.write(f"**Mentor:** {c['mentor']}")

        st.divider()
        
        # KPI Progress Section
        st.subheader("KPI Progress")
        with get_conn() as conn:
            kpi_df = pd.read_sql(
                "SELECT category, SUM(score) as total_score FROM kpis WHERE candidate_id=? GROUP BY category",
                conn, params=(cid,)
            )

        if kpi_df.empty:
            st.warning("No KPI data found for this candidate.")
        else:
            for _, r in kpi_df.iterrows():
                limit = CATEGORY_LIMITS.get(r["category"], 100)
                progress = min(r["total_score"] / limit, 1.0)
                st.write(f"**{r['category']}** ({int(r['total_score'])} / {limit})")
                st.progress(progress)

# ---------------------------------------------------
# ADD CANDIDATE
# ---------------------------------------------------
elif menu == "Add Candidate":
    st.subheader("Manual Entry")
    with st.form("add_form"):
        c1, c2 = st.columns(2)
        cid = c1.text_input("Candidate ID (Required)")
        name = c2.text_input("Full Name")
        div = c1.text_input("Division")
        spec = c2.text_input("Specialty")
        ment = c1.text_input("Mentor")
        ph = c2.selectbox("Phase 2025", ["1", "2", "3", "N/A"])
        deg = c1.selectbox("Degree", ["BS", "MS", "PhD"])
        nat = c2.text_input("Nationality")
        rem = st.text_area("Remarks")
        
        if st.form_submit_button("Save Candidate"):
            if cid:
                success = add_candidate((cid, name, div, spec, ment, None, None, None, ph, None, deg, nat, rem))
                if success: st.success("Added successfully!")
            else:
                st.error("ID is required.")

# ---------------------------------------------------
# IMPORT / EXPORT
# ---------------------------------------------------
elif menu == "Import / Export":
    st.subheader("Excel Integration")
    
    # IMPORT LOGIC
    uploaded = st.file_uploader("Upload Master Excel", type="xlsx")
    if uploaded:
        try:
            # Using openpyxl engine specifically for Streamlit Cloud compatibility
            df_upload = pd.read_excel(uploaded, engine="openpyxl")
            df_upload.columns = df_upload.columns.str.strip()
            
            with get_conn() as conn:
                existing = set(pd.read_sql("SELECT candidate_id FROM candidates", conn)["candidate_id"].astype(str))
                
                count = 0
                for _, r in df_upload.iterrows():
                    curr_id = str(r.get("ID#"))
                    if curr_id not in existing and curr_id != "None":
                        conn.execute("""
                            INSERT INTO candidates (candidate_id, name, division, specialty, mentor, phase_2025, degree, nationality, remarks)
                            VALUES (?,?,?,?,?,?,?,?,?)""",
                            (curr_id, r.get("Name"), r.get("Division"), r.get("Specialty"), r.get("Mentor"), r.get("Phase in RDP 2025"), r.get("MS/PhD"), r.get("Nationality"), r.get("Remarks"))
                        )
                        count += 1
                conn.commit()
            st.success(f"Successfully imported {count} new records!")
        except Exception as e:
            st.error(f"Error processing file: {e}")

    st.divider()

    # EXPORT LOGIC
    st.subheader("Export Data")
    if st.button("Prepare Download"):
        with get_conn() as conn:
            export_df = pd.read_sql("SELECT * FROM candidates", conn)
        
        # Proper buffer handling for openpyxl export
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            export_df.to_excel(writer, index=False, sheet_name='Candidates')
        
        st.download_button(
            label="Download Excel Report",
            data=output.getvalue(),
            file_name="RDP_Export.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# ---------------------------------------------------
# ANALYTICS
# ---------------------------------------------------
elif menu == "Analytics":
    st.subheader("RDP Distribution")
    df_stats = fetch_candidates()
    
    if not df_stats.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.write("Candidates by Phase")
            st.bar_chart(df_stats["phase_2025"].value_counts())
        with col2:
            st.write("Candidates by Degree")
            st.pie_chart(df_stats["degree"].value_counts())
    else:
        st.info("No data available for analytics.")

st.sidebar.markdown("---")
st.sidebar.caption("System: SQLite + Streamlit | Version 2.0")
