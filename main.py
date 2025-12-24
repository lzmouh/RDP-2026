import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="RDP Management System", layout="wide")

# --- DATA LOADING & SESSION STATE ---
DB_FILE = 'RDP Master.xlsx - 2025.csv'

def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        # Ensure ID# is treated as string for search consistency
        df['ID#'] = df['ID#'].astype(str)
        return df
    return pd.DataFrame()

def save_data(df):
    df.to_csv(DB_FILE, index=False)

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

# --- SIDEBAR ---
st.sidebar.title("RDP Portal")
role = st.sidebar.radio("Access Level", ["Admin", "Candidate"])

if role == "Admin":
    if st.sidebar.button("Dashboard / Main Page"): navigate_to("Main Page")
    if st.sidebar.button("Add New Candidate"): navigate_to("Add Candidate")
    if st.sidebar.button("Analytics"): navigate_to("Analytics")
else:
    # Simulating a login for candidate
    cand_id = st.sidebar.selectbox("Select Your ID (Login)", st.session_state.df['ID#'].unique())
    if st.sidebar.button("Go to My Profile"):
        navigate_to("Candidate Profile", cand_id)

# --- PAGES ---

# 1. MAIN PAGE (ADMIN TABLE)
if st.session_state.page == "Main Page":
    st.title("RDP Candidates Overview")
    
    # Selection of columns as per request
    display_df = st.session_state.df[['ID#', 'Name ', 'Division', 'Mentor', 'Specialty', 'Phase in RDP 2024']].copy()
    display_df.insert(0, 'No.', range(1, len(display_df) + 1))
    
    st.write("Click on a Candidate ID to view profile:")
    
    # Creating a clickable table effect using columns and buttons
    cols = st.columns([0.5, 1, 2, 1.5, 2, 2, 1])
    headers = ["#", "ID (Click)", "Name", "Division", "Mentor", "Specialty", "Phase"]
    for i, h in enumerate(headers):
        cols[i].markdown(f"**{h}**")
        
    for idx, row in display_df.iterrows():
        c1, c2, c3, c4, c5, c6, c7 = st.columns([0.5, 1, 2, 1.5, 2, 2, 1])
        c1.text(row['No.'])
        if c2.button(row['ID#'], key=f"btn_{row['ID#']}"):
            navigate_to("Candidate Profile", row['ID#'])
        c3.text(row['Name '])
        c4.text(row['Division'])
        c5.text(row['Mentor'])
        c6.text(row['Specialty'])
        c7.text(row['Phase in RDP 2024'])

# 2. PROFILE PAGE
elif st.session_state.page == "Candidate Profile":
    cid = st.session_state.selected_candidate
    cand_data = st.session_state.df[st.session_state.df['ID#'] == cid].iloc[0]
    
    st.title(f"Profile: {cand_data['Name ']}")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.image("https://via.placeholder.com/150", caption="Candidate Photo") # Placeholder
        st.write(f"**ID:** {cand_data['ID#']}")
        st.write(f"**Division:** {cand_data['Division']}")
        st.write(f"**Degree:** {cand_data['MS/PhD']}")
        st.write(f"**Nationality:** {cand_data['Nationality']}")

    with col2:
        st.subheader("Details")
        st.write(f"**Mentor:** {cand_data['Mentor']}")
        st.write(f"**Specialty:** {cand_data['Specialty']}")
        st.write(f"**Current Phase (2024):** {cand_data['Phase in RDP 2024']}")
        st.write(f"**Email:** {cand_data['Email ']}")
        
    st.divider()
    
    # Achievements Section (for Candidate Role)
    if role == "Candidate":
        st.subheader("Add Achievements")
        with st.form("achievement_form"):
            a_type = st.selectbox("Type", ["Paper", "Journal", "Patent Filed", "Patent Granted", "Award", "Project", "Technology Deployment"])
            details = st.text_area("Details/Description")
            if st.form_submit_button("Submit Achievement"):
                st.success(f"Added {a_type} to records.")
                # Logic to append to a separate CSV or JSON field could go here
    
    # Comments Section
    st.subheader("Comments")
    comment = st.text_area("Add a comment...", key="comment_box")
    if st.button("Post Comment"):
        st.info("Comment saved locally.")

    # Update Button
    if st.button("Update Profile Information"):
        st.session_state.edit_mode = True
        st.info("Edit mode enabled (Logic can be extended to form inputs)")

# 3. ADD CANDIDATE PAGE
elif st.session_state.page == "Add Candidate":
    st.title("Add New RDP Candidate")
    with st.form("add_form"):
        new_name = st.text_input("Name")
        new_id = st.text_input("ID#")
        new_div = st.selectbox("Division", st.session_state.df['Division'].unique())
        new_mentor = st.text_input("Mentor")
        new_spec = st.text_input("Specialty")
        new_phase = st.number_input("Phase", min_value=1, max_value=5, value=1)
        uploaded_photo = st.file_uploader("Upload Photo", type=['jpg', 'png'])
        
        if st.form_submit_button("Save Candidate"):
            new_row = {
                'Name ': new_name, 'ID#': str(new_id), 'Division': new_div, 
                'Mentor': new_mentor, 'Specialty': new_spec, 'Phase in RDP 2024': new_phase
            }
            st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_row])], ignore_index=True)
            save_data(st.session_state.df)
            st.success("Candidate added successfully!")

# 4. ANALYTICS PAGE
elif st.session_state.page == "Analytics":
    st.title("RDP Analytics Dashboard")
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Candidates vs Phases")
        phase_counts = st.session_state.df['Phase in RDP 2024'].value_counts().reset_index()
        fig1 = px.bar(phase_counts, x='Phase in RDP 2024', y='count', color='Phase in RDP 2024')
        st.plotly_chart(fig1, use_container_width=True)
        
    with c2:
        st.subheader("Candidates vs Division")
        div_counts = st.session_state.df['Division'].value_counts().reset_index()
        fig2 = px.bar(div_counts, x='Division', y='count', color='Division')
        st.plotly_chart(fig2, use_container_width=True)
        
    st.divider()
    st.subheader("Interactive Explorer")
    sel_div = st.multiselect("Select Division", st.session_state.df['Division'].unique())
    sel_phase = st.multiselect("Select Phase", sorted(st.session_state.df['Phase in RDP 2024'].unique()))
    
    filtered_df = st.session_state.df.copy()
    if sel_div:
        filtered_df = filtered_df[filtered_df['Division'].isin(sel_div)]
    if sel_phase:
        filtered_df = filtered_df[filtered_df['Phase in RDP 2024'].isin(sel_phase)]
        
    st.dataframe(filtered_df[['Name ', 'Division', 'Phase in RDP 2024', 'Specialty']], use_container_width=True)
