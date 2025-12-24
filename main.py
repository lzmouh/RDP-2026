import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="RDP Management System", layout="wide")

# --- DATA LOADING & SESSION STATE ---
DB_FILE = 'RDP Master.xlsx'

def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        # Normalize column names: remove trailing/leading spaces
        df.columns = df.columns.str.strip()
        # Ensure ID# is treated as string for search consistency
        if 'ID#' in df.columns:
            df['ID#'] = df['ID#'].astype(str)
        return df
    return pd.DataFrame()

def save_data(df):
    df.to_csv(DB_FILE, index=False)

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = load_data()

if 'page' not in st.session_state:
    st.session_state.page = "Main Page"

if 'selected_candidate' not in st.session_state:
    st.session_state.selected_candidate = None

# --- NAVIGATION FUNCTIONS ---
def navigate_to(page, candidate_id=None):
    st.session_state.page = page
    st.session_state.selected_candidate = candidate_id
    st.rerun()

# Check if data is loaded
if st.session_state.df.empty:
    st.error(f"Error: Could not find '{DB_FILE}' or the file is empty. Please ensure the file is in the same directory as the app.")
    st.stop()

# --- SIDEBAR ---
st.sidebar.title("RDP Portal")
role = st.sidebar.radio("Access Level", ["Admin", "Candidate"])

if role == "Admin":
    if st.sidebar.button("Dashboard / Main Page"): navigate_to("Main Page")
    if st.sidebar.button("Add New Candidate"): navigate_to("Add Candidate")
    if st.sidebar.button("Analytics"): navigate_to("Analytics")
else:
    cand_id = st.sidebar.selectbox("Select Your ID (Login)", st.session_state.df['ID#'].unique())
    if st.sidebar.button("Go to My Profile"):
        navigate_to("Candidate Profile", cand_id)

# --- PAGES ---

# 1. MAIN PAGE (ADMIN TABLE)
if st.session_state.page == "Main Page":
    st.title("RDP Candidates Overview")
    
    # Columns matching the CSV headers (now stripped of spaces)
    required_cols = ['ID#', 'Name', 'Division', 'Mentor', 'Specialty', 'Phase in RDP 2024']
    
    # Filter only available columns to prevent crashes
    available_cols = [c for c in required_cols if c in st.session_state.df.columns]
    display_df = st.session_state.df[available_cols].copy()
    display_df.insert(0, 'No.', range(1, len(display_df) + 1))
    
    st.write("Click on a Candidate ID to view profile:")
    
    # Header Row
    cols = st.columns([0.5, 1, 2, 1.5, 2, 2, 1])
    headers = ["#", "ID", "Name", "Division", "Mentor", "Specialty", "Phase"]
    for i, h in enumerate(headers):
        cols[i].markdown(f"**{h}**")
        
    # Data Rows
    for idx, row in display_df.iterrows():
        c1, c2, c3, c4, c5, c6, c7 = st.columns([0.5, 1, 2, 1.5, 2, 2, 1])
        c1.text(row.get('No.', ''))
        if c2.button(str(row.get('ID#', '')), key=f"btn_{row.get('ID#')}_{idx}"):
            navigate_to("Candidate Profile", row.get('ID#'))
        c3.text(row.get('Name', ''))
        c4.text(row.get('Division', ''))
        c5.text(row.get('Mentor', ''))
        c6.text(row.get('Specialty', ''))
        c7.text(row.get('Phase in RDP 2024', ''))

# 2. PROFILE PAGE
elif st.session_state.page == "Candidate Profile":
    cid = st.session_state.selected_candidate
    cand_data = st.session_state.df[st.session_state.df['ID#'] == cid].iloc[0]
    
    st.title(f"Profile: {cand_data.get('Name', 'Unknown')}")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image("https://via.placeholder.com/150", caption="Candidate Photo")
        st.write(f"**ID:** {cand_data.get('ID#')}")
        st.write(f"**Division:** {cand_data.get('Division')}")
        st.write(f"**Degree:** {cand_data.get('MS/PhD')}")

    with col2:
        st.subheader("Details")
        st.write(f"**Mentor:** {cand_data.get('Mentor')}")
        st.write(f"**Specialty:** {cand_data.get('Specialty')}")
        st.write(f"**Current Phase:** {cand_data.get('Phase in RDP 2024')}")
        st.write(f"**Email:** {cand_data.get('Email')}")
        
    st.divider()
    if role == "Candidate":
        st.subheader("Add Achievements")
        with st.form("achievement_form"):
            a_type = st.selectbox("Type", ["Paper", "Journal", "Patent Filed", "Award", "Technology Deployment"])
            details = st.text_area("Details")
            if st.form_submit_button("Submit"):
                st.success("Achievement recorded.")
    
    st.subheader("Comments")
    st.text_area("Add a comment...")
    if st.button("Update Profile Information"):
        st.info("Update logic triggered.")

# 3. ADD CANDIDATE PAGE
elif st.session_state.page == "Add Candidate":
    st.title("Add New RDP Candidate")
    with st.form("add_form"):
        new_name = st.text_input("Name")
        new_id = st.text_input("ID#")
        new_div = st.selectbox("Division", st.session_state.df['Division'].unique() if 'Division' in st.session_state.df.columns else ["N/A"])
        if st.form_submit_button("Save Candidate"):
            new_row = {'Name': new_name, 'ID#': str(new_id), 'Division': new_div}
            st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_row])], ignore_index=True)
            save_data(st.session_state.df)
            st.success("Added!")

# 4. ANALYTICS PAGE
elif st.session_state.page == "Analytics":
    st.title("RDP Analytics Dashboard")
    df = st.session_state.df
    
    c1, c2 = st.columns(2)
    with c1:
        if 'Phase in RDP 2024' in df.columns:
            fig1 = px.bar(df['Phase in RDP 2024'].value_counts().reset_index(), x='Phase in RDP 2024', y='count', title="Candidates by Phase")
            st.plotly_chart(fig1, use_container_width=True)
    with c2:
        if 'Division' in df.columns:
            fig2 = px.bar(df['Division'].value_counts().reset_index(), x='Division', y='count', title="Candidates by Division")
            st.plotly_chart(fig2, use_container_width=True)
