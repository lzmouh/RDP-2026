import streamlit as st
import pandas as pd
import database as db

# --- SETUP ---
st.set_page_config(page_title="RDP Management System", layout="wide")
db.init_db()

# --- URL PARAMETER & SESSION STATE LOGIC ---
# This part handles the "Clickable Link" logic
query_params = st.query_params

if "id" in query_params:
    # If the user clicked a link like ?id=810287
    clicked_id = query_params["id"]
    st.session_state.active_id = clicked_id
    st.session_state.menu_index = 1  # Switch to Profile Tab
    # Clear params so it doesn't keep resetting every rerun
    st.query_params.clear()

if "active_id" not in st.session_state:
    st.session_state.active_id = None
if "menu_index" not in st.session_state:
    st.session_state.menu_index = 0

# --- HELPERS ---
def clean_val(val):
    if pd.isna(val) or str(val).lower() in ["none", "nan", ""]:
        return ""
    return str(val).split('.')[0] if isinstance(val, float) else str(val)

def get_last_known_phase(row):
    for year in ['phase_2025', 'phase_2024', 'phase_2023', 'phase_2022']:
        val = clean_val(row.get(year))
        if val != "":
            return f"Phase {val} ({year.split('_')[1]})"
    return "Not Assigned"

# --- SIDEBAR MENU ---
with st.sidebar:
    st.title("RDP Portal")
    menu_choice = st.radio(
        "Menu Navigation",
        ["📊 Dashboard", "👤 Candidate Profile", "⚙️ Administration"],
        index=st.session_state.menu_index
    )
    # Sync internal state if manual click occurs
    menu_map = {"📊 Dashboard": 0, "👤 Candidate Profile": 1, "⚙️ Administration": 2}
    st.session_state.menu_index = menu_map[menu_choice]

# --- MODULES ---

if menu_choice == "📊 Dashboard":
    st.subheader("Candidate Search & Dashboard")
    
    search = st.text_input("🔍 Filter by Name, ID, or Mentor...", "")
    df = db.get_all_candidates(search)
    
    if not df.empty:
        df['Last Known Phase'] = df.apply(get_last_known_phase, axis=1)
        
        # 1. Prepare Display Data
        display_df = df[['candidate_id', 'name', 'specialty', 'division', 'mentor', 'Current Phase']].copy()
        display_df.insert(0, 'No.', range(1, len(display_df) + 1))
        
        # 2. Create the internal Link URL
        # This creates a link that points back to the app itself with a parameter
        display_df['link'] = display_df['candidate_id'].apply(lambda x: f"/?id={x}")

        # 3. Render Table with Clickable Link
        st.column_config.LinkColumn
        st.dataframe(
            display_df,
            column_config={
                "link": st.column_config.LinkColumn(
                    "Action", 
                    help="Click to view full profile",
                    display_text="View Profile ➡️"
                ),
                "candidate_id": "Candidate ID"
            },
            use_container_width=True,
            hide_index=True,
        )
        st.caption("Tip: Click 'View Profile' in the last column to jump to the details page.")
    else:
        st.warning("No data found. Sync via Administration.")

elif menu_choice == "👤 Candidate Profile":
    st.subheader("Candidate Detailed Profile")
    all_cands = db.get_all_candidates()
    
    if not all_cands.empty:
        # Determine which ID to show
        try:
            d_idx = all_cands.index[all_cands['candidate_id'] == st.session_state.active_id].tolist()[0]
        except:
            d_idx = 0
            
        selected_id = st.selectbox("Select Candidate:", all_cands['candidate_id'], index=d_idx)
        c = all_cands[all_cands['candidate_id'] == selected_id].iloc[0]
        
        # Layout
        col_pic, col_info = st.columns([1, 3])
        with col_pic:
            st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=180)
            st.metric("ID Number", selected_id)

        with col_info:
            st.header(clean_val(c['name']))
            m1, m2, m3 = st.columns(3)
            m1.metric("Division", clean_val(c['division']))
            m2.metric("Specialty", clean_val(c['specialty']))
            m3.metric("Status", get_last_known_phase(c))

            st.markdown("---")
            d1, d2 = st.columns(2)
            d1.write(f"👤 **Mentor:** {clean_val(c['mentor'])}")
            d2.write(f"🎓 **Degree:** {clean_val(c['degree'])}")
            
            st.markdown("---")
            st.subheader("📝 IK / OOK Comment")
            comment = clean_val(c['remarks'])
            if comment:
                st.info(comment)
            else:
                st.caption("No comments available.")
    else:
        st.error("No data available.")

elif menu_choice == "⚙️ Administration":
    st.subheader("System Administration")
    if st.button("🔄 Sync with RDP Master.xlsx"):
        db.sync_excel_to_db()
        st.success("Sync Complete!")
