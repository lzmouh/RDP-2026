import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="RDP Management System", layout="wide")

# --- 2. DATA UTILITIES ---
DB_FILE = 'RDP Master.xlsx - 2025.csv'

def process_data(df):
    """Normalize headers and clean ID strings."""
    df.columns = df.columns.str.strip()
    if 'ID#' in df.columns:
        df['ID#'] = df['ID#'].astype(str).str.strip()
    # Normalize 'Name' if there is a trailing space in CSV
    if 'Name' not in df.columns and 'Name ' in df.columns:
        df.rename(columns={'Name ': 'Name'}, inplace=True)
    return df

def load_local_data():
    if os.path.exists(DB_FILE):
        return process_data(pd.read_csv(DB_FILE))
    return None

# --- 3. SESSION STATE ---
if 'df' not in st.session_state:
    st.session_state.df = load_local_data()

if 'auth' not in st.session_state:
    st.session_state.auth = {"status": False, "role": None, "user_id": None}

if 'page' not in st.session_state:
    st.session_state.page = "Dashboard"

# --- 4. FIRST-TIME USE UPLOADER ---
if st.session_state.df is None:
    st.title("📂 RDP System Setup")
    st.info("No database found. Please upload your RDP Master file.")
    uploaded_file = st.file_uploader("Upload CSV or Excel", type=['csv', 'xlsx'])
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
            st.session_state.df = process_data(df)
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")
    st.stop()

# --- 5. AUTHENTICATION ---
def login():
    st.title("🔐 RDP Portal Login")
    t1, t2, t3 = st.tabs(["Admin", "Candidate", "Mentor"])
    with t1:
        with st.form("admin_log"):
            pw = st.text_input("Admin Password", type="password")
            if st.form_submit_button("Login"):
                if pw == "admin123":
                    st.session_state.auth = {"status": True, "role": "Admin", "user_id": "Admin"}
                    st.rerun()
                else: st.error("Wrong Password")
    with t2:
        with st.form("cand_log"):
            cid = st.text_input("ID#")
            cpw = st.text_input("Password (ID#)", type="password")
            if st.form_submit_button("Login"):
                if cid in st.session_state.df['ID#'].values and cid == cpw:
                    st.session_state.auth = {"status": True, "role": "Candidate", "user_id": cid}
                    st.rerun()
                else: st.error("Invalid credentials")
    with t3:
        with st.form("ment_log"):
            mentors = sorted(st.session_state.df['Mentor'].dropna().unique().tolist())
            mname = st.selectbox("Select Mentor", mentors)
            mpw = st.text_input("Mentor Password", type="password")
            if st.form_submit_button("Login"):
                if mpw == "mentor123":
                    st.session_state.auth = {"status": True, "role": "Mentor", "user_id": mname}
                    st.rerun()

if not st.session_state.auth["status"]:
    login()
    st.stop()

# --- 6. NAVIGATION ---
role = st.session_state.auth["role"]
st.sidebar.markdown(f"**Logged in as:** {role}")
if st.sidebar.button("Log Out"):
    st.session_state.auth = {"status": False, "role": None, "user_id": None}
    st.session_state.page = "Dashboard"
    st.rerun()

# --- 7. PAGES ---

# --- MAIN DASHBOARD (ADMIN) ---
if role == "Admin" and st.session_state.page == "Dashboard":
    nav = st.sidebar.radio("Navigation", ["Candidate List", "Analytics", "Add Candidate"])
    
    if nav == "Candidate List":
        st.title("Researcher Development Program - Master Table")
        
        # Squeezed column ratios: No, ID, Name, Div, Mentor, Spec, Phase
        ratios = [0.4, 0.8, 2, 1, 1.5, 2, 0.7]
        h_cols = st.columns(ratios)
        headers = ["#", "ID#", "Name", "Division", "Mentor", "Speciality", "Phase"]
        for i, h in enumerate(headers): h_cols[i].markdown(f"**{h}**")

        for idx, row in st.session_state.df.iterrows():
            r = st.columns(ratios)
            r[0].write(idx + 1)
            # Clickable ID Button
            if r[1].button(row['ID#'], key=f"btn_{row['ID#']}"):
                st.session_state.selected_cid = row['ID#']
                st.session_state.page = "Profile"
                st.rerun()
            r[2].write(row.get('Name', 'N/A'))
            r[3].write(row.get('Division', 'N/A'))
            r[4].write(row.get('Mentor', 'N/A'))
            r[5].write(row.get('Specialty', 'N/A'))
            r[6].write(row.get('Phase in RDP 2024', 'N/A'))

    elif nav == "Analytics":
        st.title("Program Analytics")
        c1, c2 = st.columns(2)
        with c1: st.plotly_chart(px.bar(st.session_state.df, x="Phase in RDP 2024", title="By Phase"), use_container_width=True)
        with c2: st.plotly_chart(px.bar(st.session_state.df, x="Division", title="By Division"), use_container_width=True)
        
        st.divider()
        st.subheader("Interactive Explorer")
        s_div = st.multiselect("Division", st.session_state.df['Division'].unique())
        s_ph = st.multiselect("Phase", st.session_state.df['Phase in RDP 2024'].unique())
        filt = st.session_state.df.copy()
        if s_div: filt = filt[filt['Division'].isin(s_div)]
        if s_ph: filt = filt[filt['Phase in RDP 2024'].isin(s_ph)]
        st.dataframe(filt, use_container_width=True)

    elif nav == "Add Candidate":
        st.title("Add New Candidate")
        with st.form("add_cand"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Full Name")
            cid = c1.text_input("ID#")
            div = c1.selectbox("Division", st.session_state.df['Division'].unique())
            mentor = c2.text_input("Mentor")
            spec = c2.text_input("Speciality")
            phase = c2.number_input("Current Phase", 1, 5, 1)
            photo = st.file_uploader("Upload Photo", type=['jpg', 'png'])
            if st.form_submit_button("Submit"):
                st.success("Candidate added successfully (Demo Mode)")

# --- CANDIDATE PROFILE PAGE (Admin View or Candidate Login) ---
if role == "Candidate" or (st.session_state.page == "Profile"):
    target_id = st.session_state.auth["user_id"] if role == "Candidate" else st.session_state.selected_cid
    data = st.session_state.df[st.session_state.df['ID#'] == target_id].iloc[0]

    st.title(f"Profile: {data.get('Name', 'Unknown')}")
    if role == "Admin":
        if st.button("← Back to List"):
            st.session_state.page = "Dashboard"
            st.rerun()

    # Layout for Profile
    col_img, col_info = st.columns([1, 2])
    
    with col_img:
        # Photo Placeholder
        st.image("https://www.w3schools.com/howto/img_avatar.png", width=200, caption="Researcher Image")
        st.file_uploader("Update Profile Photo", type=['png', 'jpg'])

    with col_info:
        st.subheader("Candidate Details")
        st.write(f"**ID#:** {data['ID#']}")
        st.write(f"**Division:** {data['Division']}")
        st.write(f"**Mentor:** {data['Mentor']}")
        st.write(f"**Speciality:** {data['Specialty']}")
        st.write(f"**Current Phase:** {data['Phase in RDP 2024']}")
        st.button("Update Profile Info")

    st.divider()

    # Achievements Section for Candidates
    st.subheader("🏆 Achievements")
    if role == "Candidate":
        with st.form("ach_form"):
            a_type = st.selectbox("Type", ["Paper", "Journal", "Disclosed Patent", "Filed Patent", "Granted Patent", "Award", "Project", "Development", "Demonstration", "Deployment", "Commercialization"])
            a_desc = st.text_area("Description")
            if st.form_submit_button("Add Achievement"):
                st.success("Achievement added to your record.")

    # Comment Section
    st.subheader("💬 Comments")
    st.text_area("Leave a comment or feedback...", height=100)
    st.button("Post Comment")

# --- MENTOR VIEW ---
if role == "Mentor":
    st.title(f"Mentorship Dashboard: {st.session_state.auth['user_id']}")
    mentees = st.session_state.df[st.session_state.df['Mentor'] == st.session_state.auth['user_id']]
    st.write(f"You have {len(mentees)} assigned candidates.")
    st.dataframe(mentees[['ID#', 'Name', 'Division', 'Phase in RDP 2024']], use_container_width=True)
