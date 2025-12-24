import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="RDP Management System", layout="wide")

# --- 2. DATA HANDLING FUNCTIONS ---
DB_FILE = 'RDP Master.xlsx - 2025.csv'

def process_dataframe(df):
    """Clean and normalize the dataframe columns and IDs"""
    df.columns = df.columns.str.strip()
    if 'ID#' in df.columns:
        df['ID#' ] = df['ID#'].astype(str).str.strip()
    return df

def load_local_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        return process_dataframe(df)
    return None

# --- 3. SESSION STATE INITIALIZATION ---
if 'df' not in st.session_state:
    st.session_state.df = load_local_data()

if 'auth' not in st.session_state:
    st.session_state.auth = {"status": False, "role": None, "user_id": None}

# --- 4. FIRST-TIME USE: FILE UPLOADER ---
if st.session_state.df is None:
    st.title("📂 RDP System - Initial Setup")
    st.info("No local database found. Please upload the 'RDP Master' file to initialize the system.")
    
    # Drag and Drop or File Picker
    uploaded_file = st.file_uploader("Upload RDP Master (CSV or Excel)", type=['csv', 'xlsx'])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                new_df = pd.read_csv(uploaded_file)
            else:
                new_df = pd.read_excel(uploaded_file)
            
            # Clean and store
            st.session_state.df = process_dataframe(new_df)
            st.success("Database loaded successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Error processing file: {e}")
    st.stop() # Prevent app from running further until file is provided

# --- 5. LOGIN SYSTEM ---
def login_screen():
    st.title("🔐 RDP Development Program Login")
    tab1, tab2, tab3 = st.tabs(["Admin", "Candidate", "Mentor"])
    
    with tab1:
        with st.form("admin_login"):
            pw = st.text_input("Admin Password", type="password")
            if st.form_submit_button("Login"):
                if pw == "admin123":
                    st.session_state.auth = {"status": True, "role": "Admin", "user_id": "Admin"}
                    st.rerun()
                else: st.error("Wrong password")

    with tab2:
        with st.form("cand_login"):
            c_id = st.text_input("Candidate ID#")
            c_pw = st.text_input("Password (Use ID#)", type="password")
            if st.form_submit_button("Login"):
                if c_id in st.session_state.df['ID#'].values and c_id == c_pw:
                    st.session_state.auth = {"status": True, "role": "Candidate", "user_id": c_id}
                    st.rerun()
                else: st.error("Invalid credentials")

    with tab3:
        with st.form("mentor_login"):
            mentors = sorted(st.session_state.df['Mentor'].dropna().unique().tolist())
            m_name = st.selectbox("Select Your Name", mentors)
            m_pw = st.text_input("Mentor Password", type="password")
            if st.form_submit_button("Login"):
                if m_pw == "mentor123":
                    st.session_state.auth = {"status": True, "role": "Mentor", "user_id": m_name}
                    st.rerun()
                else: st.error("Wrong password")

if not st.session_state.auth["status"]:
    login_screen()
    st.stop()

# --- 6. MAIN APPLICATION ---
df = st.session_state.df
role = st.session_state.auth["role"]

st.sidebar.success(f"Role: {role} | User: {st.session_state.auth['user_id']}")
if st.sidebar.button("Log Out"):
    st.session_state.auth = {"status": False, "role": None, "user_id": None}
    st.rerun()

# --- ADMIN VIEW ---
if role == "Admin":
    menu = st.sidebar.selectbox("Navigation", ["Main Table", "Analytics"])
    
    if menu == "Main Table":
        st.title("Candidate Master List")
        # Define display columns based on your CSV structure
        display_cols = ['ID#', 'Name', 'Division', 'Mentor', 'Specialty', 'Phase in RDP 2024']
        
        # Grid layout for clickable table
        cols = st.columns([0.5, 1, 2, 1.5, 2, 2, 1])
        headers = ["#", "ID#", "Name", "Division", "Mentor", "Specialty", "Phase"]
        for i, h in enumerate(headers): cols[i].markdown(f"**{h}**")

        for idx, row in df.iterrows():
            r = st.columns([0.5, 1, 2, 1.5, 2, 2, 1])
            r[0].write(idx + 1)
            if r[1].button(row['ID#'], key=f"id_{row['ID#']}"):
                st.session_state.selected_id = row['ID#']
                st.session_state.page = "Profile"
            r[2].write(row['Name'])
            r[3].write(row['Division'])
            r[4].write(row['Mentor'])
            r[5].write(row['Specialty'])
            r[6].write(row['Phase in RDP 2024'])

    elif menu == "Analytics":
        st.title("Interactive Analytics")
        # Charts
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.bar(df, x="Phase in RDP 2024", title="Candidates per Phase"), use_container_width=True)
        with c2:
            st.plotly_chart(px.bar(df, x="Division", title="Candidates per Division"), use_container_width=True)

# --- SHARED PROFILE VIEW ---
if role == "Candidate":
    target_id = st.session_state.auth["user_id"]
    p_data = df[df['ID#'] == target_id].iloc[0]
    st.title(f"My Profile: {p_data['Name']}")
    st.write(p_data)
    st.subheader("Update Achievements")
    st.text_area("Achievements...")
    st.button("Save")
