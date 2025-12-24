import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="RDP Portal - Secure Access", layout="wide")

# --- AUTHENTICATION CONFIG ---
ADMIN_PASSWORD = "admin123"  # Change this for security

# --- DATA LOADING ---
DB_FILE = 'RDP Master.xlsx - 2025.csv'

def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        df.columns = df.columns.str.strip()
        if 'ID#' in df.columns:
            df['ID#'] = df['ID#'].astype(str)
        return df
    return None

# Initialize Session State
if 'df' not in st.session_state:
    st.session_state.df = load_data()
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'page' not in st.session_state:
    st.session_state.page = "Main Page"

# --- LOGIN SCREEN ---
def login_screen():
    st.title("🔐 RDP Development Program Login")
    
    tab1, tab2, tab3 = st.tabs(["Admin Login", "Candidate Login", "Mentor Login"])
    
    with tab1:
        with st.form("admin_login"):
            pw = st.text_input("Admin Password", type="password")
            if st.form_submit_button("Login as Admin"):
                if pw == ADMIN_PASSWORD:
                    st.session_state.authenticated = True
                    st.session_state.user_role = "Admin"
                    st.rerun()
                else:
                    st.error("Invalid Admin Password")

    with tab2:
        with st.form("candidate_login"):
            c_id = st.text_input("Candidate ID#")
            c_pw = st.text_input("Password (Use your ID#)", type="password")
            if st.form_submit_button("Login"):
                if c_id in st.session_state.df['ID#'].values and c_id == c_pw:
                    st.session_state.authenticated = True
                    st.session_state.user_role = "Candidate"
                    st.session_state.user_id = c_id
                    st.rerun()
                else:
                    st.error("Invalid ID or Password")

    with tab3:
        with st.form("mentor_login"):
            m_name = st.text_input("Mentor Name (Exact as in DB)")
            m_pw = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                # Check if mentor exists in DB
                if m_name in st.session_state.df['Mentor'].values and m_pw == "mentor123":
                    st.session_state.authenticated = True
                    st.session_state.user_role = "Mentor"
                    st.session_state.user_id = m_name
                    st.rerun()
                else:
                    st.error("Invalid Mentor Credentials")

if not st.session_state.authenticated:
    login_screen()
    st.stop()

# --- LOGOUT BUTTON ---
if st.sidebar.button("Log Out"):
    st.session_state.authenticated = False
    st.session_state.user_role = None
    st.rerun()

# --- APP LOGIC (Only runs if authenticated) ---

role = st.session_state.user_role
st.sidebar.info(f"Logged in as: {role}")

# --- NAVIGATION ---
def navigate_to(page, candidate_id=None):
    st.session_state.page = page
    st.session_state.selected_candidate = str(candidate_id) if candidate_id else None

# --- ADMIN VIEW ---
if role == "Admin":
    menu = st.sidebar.selectbox("Menu", ["Dashboard", "Add Candidate", "Analytics"])
    
    if menu == "Dashboard":
        st.title("Admin Control Panel")
        # Display the master table with clickable IDs
        display_df = st.session_state.df[['ID#', 'Name', 'Division', 'Mentor', 'Phase in RDP 2024']]
        st.write("### All Candidates")
        for _, row in display_df.iterrows():
            col1, col2, col3 = st.columns([1, 3, 2])
            if col1.button(row['ID#'], key=row['ID#']):
                navigate_to("Profile", row['ID#'])
            col2.write(row['Name'])
            col3.write(row['Division'])

    elif menu == "Analytics":
        st.title("Program Analytics")
        fig = px.bar(st.session_state.df, x="Division", color="Phase in RDP 2024", title="Candidates by Division & Phase")
        st.plotly_chart(fig)

# --- CANDIDATE VIEW ---
elif role == "Candidate":
    st.title("Candidate Portal")
    user_id = st.session_state.user_id
    cand_data = st.session_state.df[st.session_state.df['ID#'] == user_id].iloc[0]
    
    st.subheader(f"Welcome, {cand_data['Name']}")
    
    with st.expander("Update My Profile"):
        new_email = st.text_input("Update Email", value=cand_data['Email'])
        if st.button("Save Changes"):
            st.success("Profile Updated!")

    st.subheader("Add Achievements")
    ach_type = st.selectbox("Type", ["Paper", "Patent", "Award", "Project"])
    details = st.text_area("Achievement Details")
    if st.button("Submit Achievement"):
        st.success("Achievement added to your profile for Review.")

# --- MENTOR VIEW ---
elif role == "Mentor":
    st.title(f"Mentor Portal: {st.session_state.user_id}")
    # Filter only candidates belonging to this mentor
    my_candidates = st.session_state.df[st.session_state.df['Mentor'] == st.session_state.user_id]
    
    st.write("### Your Assigned Candidates")
    if my_candidates.empty:
        st.write("No candidates assigned.")
    else:
        st.table(my_candidates[['ID#', 'Name', 'Phase in RDP 2024']])
        selected_c = st.selectbox("Select Candidate to Review", my_candidates['Name'])
        st.text_area(f"Add Mentor Comments for {selected_c}")
        if st.button("Save Review"):
            st.success("Review Saved.")

# --- PROFILE DETAIL VIEW (Shared) ---
if st.session_state.page == "Profile" and st.session_state.selected_candidate:
    st.divider()
    cid = st.session_state.selected_candidate
    data = st.session_state.df[st.session_state.df['ID#'] == cid].iloc[0]
    st.header(f"Profile: {data['Name']}")
    st.write(f"**Specialty:** {data['Specialty']}")
    st.write(f"**Current Phase:** {data['Phase in RDP 2024']}")
    if st.button("Back to Dashboard"):
        st.session_state.page = "Main Page"
        st.rerun()
