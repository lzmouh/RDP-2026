# EXPEC ARC RDP – Web App (Streamlit)
# ---------------------------------
# Deployment: Local (intranet / standalone)
# Data source: Excel (Auto-Score Calculator export)
# Roles supported: Admin / Candidate / Mentor / Committee
# ---------------------------------
# How to run locally:
#   pip install streamlit pandas openpyxl
#   streamlit run app.py

import streamlit as st
import pandas as pd

st.set_page_config(page_title="EXPEC ARC RDP Dashboard", layout="wide")

# ----------------------
# Authentication & Roles (Simple Local Version)
# ----------------------
USERS = {
    "admin": {"password": "admin123", "role": "Admin"},
    "mentor1": {"password": "mentor123", "role": "Mentor"},
    "committee1": {"password": "committee123", "role": "Committee"},
    "candidate1": {"password": "candidate123", "role": "Candidate"}
}

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("EXPEC ARC RDP – Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in USERS and USERS[username]["password"] == password:
            st.session_state.authenticated = True
            st.session_state.user = username
            st.session_state.role = USERS[username]["role"]
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

role = st.session_state.role
st.sidebar.success(f"Role: {role}")

# ----------------------
# Excel Data Loader
# ----------------------
@st.cache_data
def load_excel():
    return pd.read_excel("EXPEC_ARC_RDP_Auto_Score_Calculator.xlsx", sheet_name="Scores")

try:
    df = load_excel()
except:
    st.warning("Please upload the Excel score file")
    df = pd.DataFrame()

# ----------------------
# Sidebar Navigation (Role-Based)
# ----------------------
st.sidebar.title("Navigation")

pages = ["Dashboard"]

if role in ["Admin", "Committee", "Mentor"]:
    pages += ["Candidate Search", "Analytics & Reporting"]

if role == "Candidate":
    pages += ["My Profile"]

if role == "Admin":
    pages += ["Admin Controls"]

page = st.sidebar.radio("Go to", pages)

# ----------------------
# Dashboard Page
# ----------------------
if page == "Dashboard":
    st.title("EXPEC ARC RDP – Candidate Overview")

    if df.empty:
        st.info("No data loaded yet")
    else:
        phases = df["Phase"].unique()
        selected_phase = st.selectbox("Filter by Phase", ["All"] + list(phases))

        view_df = df if selected_phase == "All" else df[df["Phase"] == selected_phase]

        for _, row in view_df.iterrows():
            with st.expander(f"{row['Candidate']} | {row['Phase']} | {row['Discipline']}"):
                for cat, maxv in {
                    "Publications": 80,
                    "Innovation": 60,
                    "Projects": 60,
                    "Knowledge": 40,
                    "Leadership": 40
                }.items():
                    st.caption(cat)
                    st.progress(min(row[cat] / maxv, 1.0))

                st.metric("Total Score", row["Total"])

# ----------------------
# Candidate Search (Mentor / Committee / Admin)
# ----------------------
elif page == "Candidate Search":
    st.title("Candidate Search & Review")
    search = st.text_input("Search candidate")
    filtered = df[df["Candidate"].str.contains(search, case=False, na=False)]

    for _, row in filtered.iterrows():
        st.subheader(row["Candidate"])
        st.json(row.to_dict())
        st.divider()

# ----------------------
# My Profile (Candidate)
# ----------------------
elif page == "My Profile":
    st.title("My RDP Profile")
    candidate_name = st.session_state.user
    mydata = df[df["Candidate"] == candidate_name]

    if mydata.empty:
        st.warning("Profile not found")
    else:
        row = mydata.iloc[0]
        st.metric("Phase", row["Phase"])
        st.metric("Total Score", row["Total"])
        st.bar_chart(row[["Publications", "Innovation", "Projects", "Knowledge", "Leadership"]])

# ----------------------
# Analytics & Reporting
# ----------------------
elif page == "Analytics & Reporting":
    st.title("Analytics & Reporting")

    st.subheader("Candidates per Phase")
    st.bar_chart(df["Phase"].value_counts())

    st.subheader("Average Category Scores")
    st.bar_chart(df[["Publications", "Innovation", "Projects", "Knowledge", "Leadership"]].mean())

    st.subheader("Export")
    st.download_button("Download CSV", df.to_csv(index=False), "RDP_Report.csv")

# ----------------------
# Admin Controls
# ----------------------
elif page == "Admin Controls":
    st.title("Admin Controls")
    st.info("Upload new Excel score file to refresh dashboard")
    upload = st.file_uploader("Upload Excel", type=["xlsx"])

    if upload:
        new_df = pd.read_excel(upload)
        new_df.to_excel("EXPEC_ARC_RDP_Auto_Score_Calculator.xlsx", index=False)
        st.success("Data updated – please refresh")

# ----------------------
# Footer
# ----------------------
st.caption("EXPEC ARC RDP – Local Deployment | Excel-backed | Role-based Access")
