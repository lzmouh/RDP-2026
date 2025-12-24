import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="RDP Management System", layout="wide")

# --- AUTH CONFIG ---
ADMIN_PASSWORD = "admin123"
MENTOR_DEFAULT_PW = "mentor123"

# --- DATA LOADING ---
DB_FILE = 'RDP Master.xlsx - 2025.csv'

@st.cache_data
def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        # CRITICAL FIX: Strip all leading/trailing spaces from column headers
        df.columns = df.columns.str.strip()
        # Ensure ID# is string and cleaned
        if 'ID#' in df.columns:
            df['ID#'] = df['ID#'].astype(str).str.strip()
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
    st.session_state.page = "Main"

# --- LOGIN SCREEN ---
def login_screen():
    st.title("🚀 RDP Researcher Development Portal")
    
    tab1, tab2, tab3 = st.tabs(["Admin Access", "Candidate Access", "Mentor Access"])
    
    with tab1:
        with st.form("admin_login"):
            pw = st.text_input("Password", type="password")
            if st.form_submit_button("Login as Admin"):
                if pw == ADMIN_PASSWORD:
                    st.session_state.authenticated = True
                    st.session_state.user_role = "Admin"
                    st.rerun()
                else: st.error("Incorrect Admin Password")

    with tab2:
        with st.form("cand_login"):
            c_id = st.text_input("Candidate ID#")
            c_pw = st.text_input("Password (Use your ID#)", type="password")
            if st.form_submit_button("Login"):
                if c_id in st.session_state.df['ID#'].values and c_id == c_pw:
                    st.session_state.authenticated = True
                    st.session_state.user_role = "Candidate"
                    st.session_state.user_id = c_id
                    st.rerun()
                else: st.error("Invalid ID or Password")

    with tab3:
        with st.form("mentor_login"):
            m_list = sorted(st.session_state.df['Mentor'].dropna().unique().tolist())
            m_name = st.selectbox("Select Your Name", m_list)
            m_pw = st.text_input("Password", type="password")
            if st.form_submit_button("Login as Mentor"):
                if m_pw == MENTOR_DEFAULT_PW:
                    st.session_state.authenticated = True
                    st.session_state.user_role = "Mentor"
                    st.session_state.user_id = m_name
                    st.rerun()
                else: st.error("Incorrect Mentor Password")

if not st.session_state.authenticated:
    login_screen()
    st.stop()

# --- SIDEBAR & LOGOUT ---
st.sidebar.subheader(f"Logged in as: {st.session_state.user_role}")
if st.sidebar.button("Log Out"):
    st.session_state.authenticated = False
    st.rerun()

df = st.session_state.df

# --- NAVIGATION ---
if st.session_state.user_role == "Admin":
    choice = st.sidebar.radio("Navigation", ["Candidate Table", "Add Candidate", "Analytics"])
elif st.session_state.user_role == "Mentor":
    choice = "Mentor View"
else:
    choice = "My Profile"

# --- 1. ADMIN TABLE ---
if choice == "Candidate Table":
    st.title("Program Participants Overview")
    
    # Select specific columns to display
    cols_to_show = ['ID#', 'Name', 'Division', 'Mentor', 'Specialty', 'Phase in RDP 2024']
    display_df = df[cols_to_show].copy()
    display_df.insert(0, 'No.', range(1, len(display_df) + 1))
    
    # Custom interactive table headers
    h_cols = st.columns([0.5, 1, 2, 1.5, 2, 2, 1])
    headers = ["#", "ID#", "Name", "Division", "Mentor", "Specialty", "Phase"]
    for i, h in enumerate(headers): h_cols[i].markdown(f"**{h}**")
    
    for _, row in display_df.iterrows():
        r_cols = st.columns([0.5, 1, 2, 1.5, 2, 2, 1])
        r_cols[0].write(row['No.'])
        if r_cols[1].button(row['ID#'], key=f"btn_{row['ID#']}"):
            st.session_state.page = "Profile"
            st.session_state.selected_id = row['ID#']
            st.rerun()
        r_cols[2].write(row['Name'])
        r_cols[3].write(row['Division'])
        r_cols[4].write(row['Mentor'])
        r_cols[5].write(row['Specialty'])
        r_cols[6].write(row['Phase in RDP 2024'])

# --- 2. ANALYTICS ---
elif choice == "Analytics":
    st.title("RDP Program Analytics")
    c1, c2 = st.columns(2)
    with c1:
        fig1 = px.bar(df, x='Phase in RDP 2024', title="Candidates vs Phase", color='Phase in RDP 2024')
        st.plotly_chart(fig1, use_container_width=True)
    with c2:
        fig2 = px.bar(df, x='Division', title="Candidates vs Division", color='Division')
        st.plotly_chart(fig2, use_container_width=True)
    
    st.divider()
    st.subheader("Interactive Explorer")
    sel_div = st.multiselect("Filter by Division", options=df['Division'].unique())
    sel_ph = st.multiselect("Filter by Phase", options=sorted(df['Phase in RDP 2024'].unique()))
    
    filt_df = df.copy()
    if sel_div: filt_df = filt_df[filt_df['Division'].isin(sel_div)]
    if sel_ph: filt_df = filt_df[filt_df['Phase in RDP 2024'].isin(sel_ph)]
    st.dataframe(filt_df)

# --- 3. MENTOR VIEW ---
elif choice == "Mentor View":
    st.title(f"Candidates Assigned to {st.session_state.user_id}")
    mentor_df = df[df['Mentor'] == st.session_state.user_id]
    st.table(mentor_df[['ID#', 'Name', 'Division', 'Phase in RDP 2024']])

# --- 4. PROFILE PAGE (Drill-down or Candidate View) ---
if choice == "My Profile" or (st.session_state.page == "Profile"):
    target_id = st.session_state.user_id if choice == "My Profile" else st.session_state.selected_id
    cand_data = df[df['ID#'] == target_id].iloc[0]
    
    st.title(f"Profile: {cand_data['Name']}")
    
    col_img, col_txt = st.columns([1, 2])
    with col_img:
        st.image("https://via.placeholder.com/150", caption=f"ID: {target_id}")
        st.file_uploader("Update Photo", type=['jpg', 'png'])
        
    with col_txt:
        st.write(f"**Division:** {cand_data['Division']}")
        st.write(f"**Mentor:** {cand_data['Mentor']}")
        st.write(f"**Specialty:** {cand_data['Specialty']}")
        st.write(f"**Email:** {cand_data['Email']}")
    
    st.subheader("Achievements")
    st.text_area("Add (Paper, Journal, Patent, Award, Projects, etc.)")
    if st.button("Update Profile"):
        st.success("Profile saved.")
    
    if st.session_state.page == "Profile" and st.session_state.user_role == "Admin":
        if st.button("Return to Table"):
            st.session_state.page = "Main"
            st.rerun()
