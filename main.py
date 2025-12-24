import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="RDP Researcher Development Program", layout="wide")

# --- FILE CONFIG ---
# This is the expected filename. Ensure your file is named exactly this or use the uploader.
DB_FILE = 'RDP Master.xlsx - 2025.csv'

# --- DATA LOADING ---
def load_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            # Clean column names (remove leading/trailing spaces)
            df.columns = df.columns.str.strip()
            # Ensure ID# is a string for search
            if 'ID#' in df.columns:
                df['ID#'] = df['ID#'].astype(str)
            return df
        except Exception as e:
            st.error(f"Error reading file: {e}")
            return None
    return None

# Initialize Session State
if 'df' not in st.session_state:
    st.session_state.df = load_data()

if 'page' not in st.session_state:
    st.session_state.page = "Main Page"

if 'selected_candidate' not in st.session_state:
    st.session_state.selected_candidate = None

# Logic for data persistence (Session-based for demo)
if 'achievements' not in st.session_state:
    st.session_state.achievements = {} # ID -> list of dicts

# --- NAVIGATION ---
def navigate_to(page, candidate_id=None):
    st.session_state.page = page
    st.session_state.selected_candidate = str(candidate_id) if candidate_id else None
    st.rerun()

# --- HEADER & FILE UPLOAD ---
if st.session_state.df is None:
    st.title("🚀 RDP System Setup")
    st.warning(f"File '{DB_FILE}' not found in the directory.")
    uploaded_file = st.file_uploader("Please upload the RDP Master CSV file to start", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip()
        if 'ID#' in df.columns:
            df['ID#'] = df['ID#'].astype(str)
        st.session_state.df = df
        st.success("File uploaded successfully!")
        st.rerun()
    st.stop()

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("RDP Navigation")
role = st.sidebar.radio("Role", ["Admin", "Candidate"])

if role == "Admin":
    if st.sidebar.button("📋 Candidate List (Main)"): navigate_to("Main Page")
    if st.sidebar.button("➕ Add Candidate"): navigate_to("Add Candidate")
    if st.sidebar.button("📊 Analytics"): navigate_to("Analytics")
else:
    # Candidate "Login"
    all_ids = sorted(st.session_state.df['ID#'].unique().tolist())
    my_id = st.sidebar.selectbox("Select Your ID", all_ids)
    if st.sidebar.button("👤 View My Profile"):
        navigate_to("Candidate Profile", my_id)

# --- PAGES ---

# 1. MAIN PAGE (ADMIN TABLE)
if st.session_state.page == "Main Page":
    st.title("Researcher Development Program - Admin Dashboard")
    
    # Define phase column (Mapping 'current phase' to 2024 data as it is most complete)
    phase_col = 'Phase in RDP 2024'
    
    # Prepare display data
    display_df = st.session_state.df[['ID#', 'Name', 'Division', 'Mentor', 'Specialty', phase_col]].copy()
    display_df.insert(0, 'No.', range(1, len(display_df) + 1))
    
    # Custom Table UI
    cols = st.columns([0.5, 1, 2, 1.5, 2, 2, 1])
    headers = ["#", "ID#", "Candidate Name", "Division", "Mentor", "Specialty", "Phase"]
    for i, h in enumerate(headers):
        cols[i].markdown(f"**{h}**")
    
    for _, row in display_df.iterrows():
        c1, c2, c3, c4, c5, c6, c7 = st.columns([0.5, 1, 2, 1.5, 2, 2, 1])
        c1.text(row['No.'])
        # Clickable ID
        if c2.button(row['ID#'], key=f"id_{row['ID#']}"):
            navigate_to("Candidate Profile", row['ID#'])
        c3.text(row['Name'])
        c4.text(row['Division'])
        c5.text(row['Mentor'])
        c6.text(row['Specialty'])
        c7.text(row[phase_col])

# 2. PROFILE PAGE
elif st.session_state.page == "Candidate Profile":
    cid = st.session_state.selected_candidate
    row = st.session_state.df[st.session_state.df['ID#'] == cid].iloc[0]
    
    st.title(f"Profile: {row['Name']}")
    
    col_img, col_info = st.columns([1, 3])
    with col_img:
        st.image("https://via.placeholder.com/200", caption=f"ID: {cid}")
        if st.button("Update Profile Photo"):
            st.info("Photo upload feature triggered.")
            
    with col_info:
        st.subheader("Professional Details")
        st.write(f"**Division:** {row['Division']}")
        st.write(f"**Mentor:** {row['Mentor']}")
        st.write(f"**Specialty:** {row['Specialty']}")
        st.write(f"**Current Phase (2024):** {row['Phase in RDP 2024']}")
        st.write(f"**Email:** {row['Email']}")
        st.write(f"**Nationality:** {row['Nationality']}")

    st.divider()
    
    # Achievements Section
    st.subheader("🏆 Achievements")
    if cid not in st.session_state.achievements:
        st.session_state.achievements[cid] = []
    
    if st.session_state.achievements[cid]:
        for ach in st.session_state.achievements[cid]:
            st.info(f"**{ach['type']}**: {ach['details']}")
    else:
        st.write("No achievements listed yet.")

    # Add Achievements (Visible to Candidate or Admin)
    with st.expander("Add New Achievement"):
        with st.form("ach_form"):
            a_type = st.selectbox("Type", ["Paper", "Journal", "Disclosed Patent", "Filed Patent", "Granted Patent", "Award", "Project", "Technology Deployment", "Commercialization"])
            a_details = st.text_area("Details (Title, Year, etc.)")
            if st.form_submit_button("Save Achievement"):
                st.session_state.achievements[cid].append({"type": a_type, "details": a_details})
                st.success("Achievement saved!")
                st.rerun()

    st.divider()
    st.subheader("💬 Comments")
    st.text_area("Admin/Mentor Comments", height=100)
    
    if st.button("Update Profile Data"):
        st.warning("Editing fields is enabled in the full database version.")

# 3. ANALYTICS PAGE
elif st.session_state.page == "Analytics":
    st.title("📊 Researcher Development Analytics")
    df = st.session_state.df
    
    # 1. Row of Bar Charts
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Candidates vs Phases")
        fig1 = px.bar(df['Phase in RDP 2024'].value_counts().reset_index(), 
                     x='Phase in RDP 2024', y='count', color='Phase in RDP 2024',
                     labels={'count': 'Number of Candidates'})
        st.plotly_chart(fig1, use_container_width=True)
        
    with col2:
        st.subheader("Candidates vs Division")
        fig2 = px.bar(df['Division'].value_counts().reset_index(), 
                     x='Division', y='count', color='Division')
        st.plotly_chart(fig2, use_container_width=True)
        
    st.divider()
    
    # 2. Interactive Selector Chart
    st.subheader("Interactive Explorer")
    sel_div = st.multiselect("Select Divisions", options=sorted(df['Division'].unique()), default=sorted(df['Division'].unique())[:3])
    sel_phase = st.multiselect("Select Phases", options=sorted(df['Phase in RDP 2024'].unique()), default=sorted(df['Phase in RDP 2024'].unique()))
    
    filtered_df = df[df['Division'].isin(sel_div) & df['Phase in RDP 2024'].isin(sel_phase)]
    
    if not filtered_df.empty:
        fig3 = px.scatter(filtered_df, x="Division", y="Name", color="Phase in RDP 2024", 
                         title="Filtered Candidate Mapping", height=600)
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.write("No candidates match the selection.")

# 4. ADD CANDIDATE PAGE
elif st.session_state.page == "Add Candidate":
    st.title("➕ Register New Candidate")
    with st.form("new_cand"):
        c1, c2 = st.columns(2)
        with c1:
            n_name = st.text_input("Full Name")
            n_id = st.text_input("ID#")
            n_div = st.selectbox("Division", sorted(st.session_state.df['Division'].unique()))
        with c2:
            n_mentor = st.text_input("Mentor Name")
            n_spec = st.text_input("Speciality")
            n_phase = st.slider("Current Phase", 1, 4, 1)
        
        n_photo = st.file_uploader("Upload Profile Photo", type=["jpg", "png"])
        
        if st.form_submit_button("Add to Database"):
            # logic to append to session df
            new_data = {
                'Name': n_name, 'ID#': n_id, 'Division': n_div, 
                'Mentor': n_mentor, 'Specialty': n_spec, 'Phase in RDP 2024': n_phase,
                'Email': '', 'Nationality': ''
            }
            st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_data])], ignore_index=True)
            st.success(f"Candidate {n_name} added successfully!")
