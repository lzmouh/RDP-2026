import streamlit as st
import pandas as pd
import database as db

# --- SETUP ---
st.set_page_config(page_title="RDP Management System", layout="wide")
db.init_db()

# --- SESSION STATE MANAGEMENT ---
if "active_id" not in st.session_state:
    st.session_state.active_id = None
if "menu_index" not in st.session_state:
    st.session_state.menu_index = 0

def navigate_to_profile(cid):
    st.session_state.active_id = cid
    st.session_state.menu_index = 1 # Index of '👤 Candidate Profile'

# --- HELPERS ---
def clean_val(val):
    if pd.isna(val) or str(val).lower() in ["none", "nan", ""]:
        return ""
    return str(val).split('.')[0] if isinstance(val, float) else str(val)

def get_last_known_phase(row):
    for year in ['phase_2025', 'phase_2024', 'phase_2023', 'phase_2022']:
        val = clean_val(row.get(year))
        if val != "":
            y = year.split('_')[1]
            return f"Phase {val} ({y})"
    return "Not Assigned"

# --- SIDEBAR MENU ---
with st.sidebar:
    st.title("RDP Portal")
    menu_choice = st.radio(
        "Menu Navigation",
        ["📊 Dashboard", "👤 Candidate Profile", "⚙️ Administration"],
        index=st.session_state.menu_index,
        key="main_menu"
    )
    # Sync internal index if user clicks manually
    menu_map = {"📊 Dashboard": 0, "👤 Candidate Profile": 1, "⚙️ Administration": 2}
    st.session_state.menu_index = menu_map[menu_choice]
    
    st.divider()
    if st.session_state.active_id:
        st.info(f"Viewing: {st.session_state.active_id}")

# --- MODULES ---

if menu_choice == "📊 Dashboard":
    st.subheader("Candidate Search & Dashboard")
    
    # 1. Selection Link Logic
    all_data = db.get_all_candidates()
    if not all_data.empty:
        col_search, col_link = st.columns([2, 1])
        with col_search:
            search = st.text_input("🔍 Filter by Name, ID, or Mentor...", "")
        with col_link:
            # THIS IS THE "LINK"
            target = st.selectbox("🔗 Quick Link: Select ID to view Profile", 
                                ["Select..."] + all_data['candidate_id'].tolist())
            if target != "Select...":
                navigate_to_profile(target)
                st.rerun()

        # 2. Process Dashboard Table
        df = db.get_all_candidates(search)
        if not df.empty:
            df['Last Known Phase'] = df.apply(get_last_known_phase, axis=1)
            
            # Formatting: Add Index + Select columns
            display_df = df[['candidate_id', 'name', 'specialty', 'division', 'mentor', 'Last Known Phase']].copy()
            display_df.insert(0, 'No.', range(1, len(display_df) + 1)) # Add Index First Column
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.warning("No data found. Go to Administration to Sync with Excel.")

elif menu_choice == "👤 Candidate Profile":
    st.subheader("Candidate Detailed Profile")
    all_cands = db.get_all_candidates()
    
    if not all_cands.empty:
        # Resolve selection
        try:
            d_idx = all_cands.index[all_cands['candidate_id'] == st.session_state.active_id].tolist()[0]
        except:
            d_idx = 0
            
        selected_id = st.selectbox("Switch Candidate:", all_cands['candidate_id'], index=d_idx)
        c = all_cands[all_cands['candidate_id'] == selected_id].iloc[0]
        st.session_state.active_id = selected_id
        
        # Profile View
        col_pic, col_info = st.columns([1, 3])
        with col_pic:
            st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=180)
            st.metric("ID Number", selected_id)

        with col_info:
            st.header(clean_val(c['name']))
            
            # Metrics
            m1, m2, m3 = st.columns(3)
            m1.metric("Division", clean_val(c['division']))
            m2.metric("Specialty", clean_val(c['specialty']))
            m3.metric("Status", get_last_known_phase(c))

            st.markdown("---")
            d1, d2 = st.columns(2)
            d1.write(f"👤 **Mentor:** {clean_val(c['mentor'])}")
            d2.write(f"🎓 **Degree:** {clean_val(c['degree'])}")
            
            st.markdown("---")
            # IK/OOK Comment Section
            st.subheader("📝 IK / OOK Comment")
            comment = clean_val(c['remarks'])
            if comment:
                st.info(comment)
            else:
                st.caption("No comments available for this candidate.")
    else:
        st.error("Please load data in the Admin tab first.")

elif menu_choice == "⚙️ Administration":
    st.subheader("System Administration")
    if st.button("🔄 Sync with RDP Master.xlsx"):
        result = db.sync_excel_to_db()
        if result is True:
            st.success("Database synchronized successfully!")
        else:
            st.error(f"Sync failed: {result}")
