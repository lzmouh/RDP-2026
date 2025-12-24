import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- 1. PAGE CONFIG & STYLING ---
st.set_page_config(page_title="RDP Researcher Portal", layout="wide")

# --- 2. DATA LOADING (Handles Column Name Errors) ---
DB_FILE = 'RDP Master.xlsx'

def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        # Normalize headers to fix KeyErrors (removes trailing spaces)
        df.columns = df.columns.str.strip()
        # Ensure ID# is a string for matching
        if 'ID#' in df.columns:
            df['ID#'] = df['ID#'].astype(str).str.strip()
        return df
    return None

# --- 3. SESSION STATE INITIALIZATION ---
if 'df' not in st.session_state:
    st.session_state.df = load_data()

if 'auth' not in st.session_state:
    st.session_state.auth = {"status": False, "role": None, "user_id": None}

if 'page' not in st.session_state:
    st.session_state.page = "Dashboard"

# --- 4. LOGIN SYSTEM ---
def login_screen():
    st.title("🔐 RDP Development Program Login")
    
    if st.session_state.df is None:
        st.error("Database file not found. Please ensure 'RDP Master.xlsx - 2025.csv' is in the folder.")
        st.stop()

    tab1, tab2, tab3 = st.tabs(["Admin", "Candidate", "Mentor"])
    
    with tab1:
        with st.form("admin_form"):
            pw = st.text_input("Admin Password", type="password")
            if st.form_submit_button("Login"):
                if pw == "admin123":
                    st.session_state.auth = {"status": True, "role": "Admin", "user_id": "Admin"}
                    st.rerun()
                else: st.error("Invalid password")

    with tab2:
        with st.form("cand_form"):
            c_id = st.text_input("Candidate ID#")
            c_pw = st.text_input("Password (ID#)", type="password")
            if st.form_submit_button("Login"):
                if c_id in st.session_state.df['ID#'].values and c_id == c_pw:
                    st.session_state.auth = {"status": True, "role": "Candidate", "user_id": c_id}
                    st.rerun()
                else: st.error("ID not found or password incorrect")

    with tab3:
        with st.form("mentor_form"):
            mentors = sorted(st.session_state.df['Mentor'].dropna().unique().tolist())
            m_name = st.selectbox("Select Your Name", mentors)
            m_pw = st.text_input("Mentor Password", type="password")
            if st.form_submit_button("Login"):
                if m_pw == "mentor123":
                    st.session_state.auth = {"status": True, "role": "Mentor", "user_id": m_name}
                    st.rerun()
                else: st.error("Incorrect Mentor password")

# --- 5. MAIN APP FLOW ---
if not st.session_state.auth["status"]:
    login_screen()
else:
    # Sidebar Navigation
    role = st.session_state.auth["role"]
    st.sidebar.title(f"Welcome, {st.session_state.auth['user_id']}")
    
    if st.sidebar.button("🚪 Logout"):
        st.session_state.auth = {"status": False, "role": None, "user_id": None}
        st.rerun()

    df = st.session_state.df

    # --- ADMIN VIEW ---
    if role == "Admin":
        menu = st.sidebar.radio("Navigation", ["Candidate List", "Analytics", "Add Candidate"])
        
        if menu == "Candidate List":
            st.title("Program Candidates")
            cols_to_show = ['ID#', 'Name', 'Division', 'Mentor', 'Specialty', 'Phase in RDP 2024']
            
            # Display Header
            h = st.columns([0.5, 1, 2, 1.5, 2, 2, 1])
            labels = ["#", "ID#", "Name", "Division", "Mentor", "Specialty", "Phase"]
            for i, label in enumerate(labels): h[i].markdown(f"**{label}**")

            # Display Rows
            for idx, row in df[cols_to_show].iterrows():
                r = st.columns([0.5, 1, 2, 1.5, 2, 2, 1])
                r[0].write(idx + 1)
                if r[1].button(row['ID#'], key=f"btn_{row['ID#']}"):
                    st.session_state.page = "Profile"
                    st.session_state.selected_id = row['ID#']
                r[2].write(row['Name'])
                r[3].write(row['Division'])
                r[4].write(row['Mentor'])
                r[5].write(row['Specialty'])
                r[6].write(row['Phase in RDP 2024'])

        elif menu == "Analytics":
            st.title("Analytics Dashboard")
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(px.bar(df, x="Phase in RDP 2024", color="Phase in RDP 2024", title="Candidates by Phase"))
            with c2:
                st.plotly_chart(px.bar(df, x="Division", color="Division", title="Candidates by Division"))
            
            st.subheader("Interactive Explorer")
            d_filter = st.multiselect("Select Division", df['Division'].unique())
            p_filter = st.multiselect("Select Phase", df['Phase in RDP 2024'].unique())
            filtered = df.copy()
            if d_filter: filtered = filtered[filtered['Division'].isin(d_filter)]
            if p_filter: filtered = filtered[filtered['Phase in RDP 2024'].isin(p_filter)]
            st.dataframe(filtered)

    # --- CANDIDATE VIEW ---
    elif role == "Candidate":
        st.title("My RDP Profile")
        user_id = st.session_state.auth["user_id"]
        data = df[df['ID#'] == user_id].iloc[0]
        
        col1, col2 = st.columns([1, 2])
        with col1:
            st.image("https://via.placeholder.com/150", caption="Profile Photo")
            st.write(f"**ID:** {user_id}")
        with col2:
            st.write(f"**Mentor:** {data['Mentor']}")
            st.write(f"**Specialty:** {data['Specialty']}")
            st.write(f"**Division:** {data['Division']}")
        
        st.subheader("Achievements")
        st.text_area("Update Achievements (Papers, Patents, Projects...)", height=150)
        if st.button("Save Achievements"):
            st.success("Achievements updated successfully!")

    # --- MENTOR VIEW ---
    elif role == "Mentor":
        st.title(f"Candidates Mentored by {st.session_state.auth['user_id']}")
        mentee_df = df[df['Mentor'] == st.session_state.auth['user_id']]
        st.dataframe(mentee_df[['ID#', 'Name', 'Division', 'Phase in RDP 2024', 'Specialty']])
        st.text_area("Add Mentor Comments/Feedback")
        st.button("Submit Feedback")

    # --- DRILL DOWN PROFILE PAGE ---
    if st.session_state.page == "Profile" and role == "Admin":
        st.divider()
        profile_id = st.session_state.selected_id
        p_data = df[df['ID#'] == profile_id].iloc[0]
        st.header(f"Profile Detail: {p_data['Name']}")
        st.write(p_data)
        if st.button("Close Profile"):
            st.session_state.page = "Dashboard"
            st.rerun()
