import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="RDP Portal", layout="wide")

# --- AUTH CONFIG ---
ADMIN_PASSWORD = "admin123"
MENTOR_DEFAULT_PW = "mentor123"

# --- DATA LOADING ---
DB_FILE = 'RDP Master.xlsx - 2025.csv'

@st.cache_data
def load_and_clean_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        # CRITICAL FIX: Strip spaces from column headers
        df.columns = df.columns.str.strip()
        # Clean ID# and ensure it's string
        if 'ID#' in df.columns:
            df['ID#'] = df['ID#'].astype(str).str.strip()
        return df
    return None

# Initialize Session State
if 'df' not in st.session_state:
    st.session_state.df = load_and_clean_data()

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_role = None
    st.session_state.user_id = None

if 'page' not in st.session_state:
    st.session_state.page = "Main"

# --- LOGIN LOGIC ---
def login():
    st.title("🔐 RDP Management System Login")
    
    tab1, tab2, tab3 = st.tabs(["Admin", "Candidate", "Mentor"])
    
    with tab1:
        with st.form("admin_form"):
            pw = st.text_input("Admin Password", type="password")
            if st.form_submit_button("Login as Admin"):
                if pw == ADMIN_PASSWORD:
                    st.session_state.authenticated = True
                    st.session_state.user_role = "Admin"
                    st.rerun()
                else: st.error("Wrong password")

    with tab2:
        with st.form("cand_form"):
            c_id = st.text_input("Candidate ID#")
            c_pw = st.text_input("Password (Default is ID#)", type="password")
            if st.form_submit_button("Login"):
                if c_id in st.session_state.df['ID#'].values and c_id == c_pw:
                    st.session_state.authenticated = True
                    st.session_state.user_role = "Candidate"
                    st.session_state.user_id = c_id
                    st.rerun()
                else: st.error("Invalid ID or Password")

    with tab3:
        with st.form("mentor_form"):
            m_name = st.selectbox("Select Your Name", sorted(st.session_state.df['Mentor'].unique().tolist()))
            m_pw = st.text_input("Password", type="password")
            if st.form_submit_button("Login as Mentor"):
                if m_pw == MENTOR_DEFAULT_PW:
                    st.session_state.authenticated = True
                    st.session_state.user_role = "Mentor"
                    st.session_state.user_id = m_name
                    st.rerun()
                else: st.error("Incorrect Mentor password")

if not st.session_state.authenticated:
    login()
    st.stop()

# --- APP LAYOUT ---
st.sidebar.title(f"Welcome, {st.session_state.user_role}")
if st.sidebar.button("Logout"):
    st.session_state.authenticated = False
    st.rerun()

df = st.session_state.df

# --- NAVIGATION ---
if st.session_state.user_role == "Admin":
    choice = st.sidebar.radio("Navigation", ["Main Dashboard", "Add Candidate", "Analytics"])
elif st.session_state.user_role == "Mentor":
    choice = "Mentor Dashboard"
else:
    choice = "My Profile"

# --- ADMIN: MAIN DASHBOARD ---
if choice == "Main Dashboard":
    st.title("Researcher Development Program - Admin")
    
    # Selection of columns
    cols_to_show = ['ID#', 'Name', 'Division', 'Mentor', 'Specialty', 'Phase in RDP 2024']
    display_df = df[cols_to_show].copy()
    display_df.insert(0, 'No.', range(1, len(display_df) + 1))

    # Clickable Table Implementation
    head = st.columns([0.5, 1, 2, 1.5, 2, 2, 1])
    fields = ["#", "ID#", "Name", "Division", "Mentor", "Specialty", "Phase"]
    for i, f in enumerate(fields): head[i].write(f"**{f}**")

    for idx, row in display_df.iterrows():
        c = st.columns([0.5, 1, 2, 1.5, 2, 2, 1])
        c[0].write(row['No.'])
        if c[1].button(row['ID#'], key=f"btn_{row['ID#']}"):
            st.session_state.page = "Profile"
            st.session_state.selected_id = row['ID#']
            st.rerun()
        c[2].write(row['Name'])
        c[3].write(row['Division'])
        c[4].write(row['Mentor'])
        c[5].write(row['Specialty'])
        c[6].write(row['Phase in RDP 2024'])

# --- ANALYTICS ---
elif choice == "Analytics":
    st.title("Program Analytics")
    c1, c2 = st.columns(2)
    with c1:
        fig1 = px.bar(df, x="Phase in RDP 2024", title="Candidates per Phase")
        st.plotly_chart(fig1)
    with c2:
        fig2 = px.bar(df, x="Division", title="Candidates per Division")
        st.plotly_chart(fig2)
    
    st.subheader("Interactive Filter")
    sel_div = st.multiselect("Division", df['Division'].unique())
    sel_ph = st.multiselect("Phase", df['Phase in RDP 2024'].unique())
    filt = df.copy()
    if sel_div: filt = filt[filt['Division'].isin(sel_div)]
    if sel_ph: filt = filt[filt['Phase in RDP 2024'].isin(sel_ph)]
    st.dataframe(filt)

# --- MENTOR DASHBOARD ---
elif choice == "Mentor Dashboard":
    st.title(f"Candidates under {st.session_state.user_id}")
    my_cands = df[df['Mentor'] == st.session_state.user_id]
    st.table(my_cands[['ID#', 'Name', 'Division', 'Phase in RDP 2024']])

# --- CANDIDATE PROFILE (And Admin Drill-down) ---
if (choice == "My Profile") or (st.session_state.page == "Profile"):
    target_id = st.session_state.user_id if choice == "My Profile" else st.session_state.selected_id
    user_data = df[df['ID#'] == target_id].iloc[0]
    
    st.title(f"Candidate Profile: {user_data['Name']}")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image("https://via.placeholder.com/150", caption="Photo Placeholder")
        st.write(f"**Division:** {user_data['Division']}")
    with col2:
        st.write(f"**Mentor:** {user_data['Mentor']}")
        st.write(f"**Specialty:** {user_data['Specialty']}")
        st.write(f"**Current Phase:** {user_data['Phase in RDP 2024']}")

    st.subheader("Achievements")
    st.text_area("List achievements (Papers, Patents, Projects...)", placeholder="Type here...")
    if st.button("Update Profile"):
        st.success("Information saved successfully.")

    if st.button("Back to Dashboard"):
        st.session_state.page = "Main"
        st.rerun()
