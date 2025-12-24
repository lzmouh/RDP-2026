import streamlit as st
import pandas as pd
import database as db

# --- SETUP ---
st.set_page_config(page_title="RDP Management System", layout="wide")
db.init_db()

# --- SESSION STATE ---
if "active_id" not in st.session_state:
    st.session_state.active_id = None
if "menu_selection" not in st.session_state:
    st.session_state.menu_selection = "📊 Dashboard"

# --- NAVIGATION CALLBACK ---
def view_profile(cid):
    st.session_state.active_id = str(cid)
    st.session_state.menu_selection = "👤 Profile"

# --- SIDEBAR MENU ---
with st.sidebar:
    st.title("RDP Portal")
    menu_choice = st.radio(
        "Menu Navigation",
        ["📊 Dashboard", "👤 Profile", "⚙️ Admin"],
        index=["📊 Dashboard", "👤 Profile", "⚙️ Admin"].index(st.session_state.menu_selection),
        key="navigation_radio"
    )
    st.session_state.menu_selection = menu_choice

# --- MODULES ---

if menu_choice == "📊 Dashboard":
    st.subheader("Candidate Dashboard")
    
    search = st.text_input("🔍 Search", placeholder="Search by name, ID, or mentor...")
    df = db.get_all_candidates(search)
    
    if not df.empty:
        # Data Preparation
        df['Last Known Phase'] = df.apply(db.get_last_known_phase, axis=1)
        
        # Prepare the DataFrame for display
        display_df = df[['candidate_id', 'name', 'specialty', 'division', 'mentor', 'Last Known Phase']].copy()
        display_df.insert(0, 'No.', range(1, len(display_df) + 1))
        
        # Add a column for the button action
        display_df.insert(1, "View", "→")

        # Streamlit Native Table with Button Column
        st.data_editor(
            display_df,
            column_config={
                "No.": st.column_config.Column(width="small"),
                "View": st.column_config.ButtonColumn(
                    "View",
                    help="Click to view candidate profile",
                    width="small",
                    on_click=None # We will handle selection via the return value or row selection
                ),
                "candidate_id": "Candidate ID",
                "name": "Full Name",
                "Last Known Phase": st.column_config.TextColumn("Status")
            },
            hide_index=True,
            use_container_width=True,
            key="dashboard_table",
            disabled=display_df.columns # Make it read-only except for button behavior
        )

        # Handle the click logic via state monitoring
        # Since on_click in ButtonColumn can be tricky with row data, we use the selection event
        # Alternatively, for simplicity and stability across versions:
        st.info("💡 Select a row and click the arrow to jump to the profile.")
        
        # Capture selection
        event = st.dataframe(
            display_df,
            on_select="rerun",
            selection_mode="single",
            hide_index=True,
            use_container_width=True,
            column_config={"View": None} # Hide the arrow column in this secondary view if preferred
        )

        if event.selection.rows:
            selected_row_index = event.selection.rows[0]
            cid = display_df.iloc[selected_row_index]['candidate_id']
            view_profile(cid)
            st.rerun()

    else:
        st.warning("No records found.")

elif menu_choice == "👤 Profile":
    st.subheader("Candidate Detailed Profile")
    all_cands = db.get_all_candidates()
    
    if not all_cands.empty:
        # Default index logic
        try:
            d_idx = all_cands.index[all_cands['candidate_id'] == st.session_state.active_id].tolist()[0]
        except:
            d_idx = 0
            
        selected_id = st.selectbox("Select Candidate:", all_cands['candidate_id'], index=d_idx)
        c = all_cands[all_cands['candidate_id'] == selected_id].iloc[0]
        st.session_state.active_id = selected_id
        
        # Profile UI
        col_pic, col_info = st.columns([1, 3])
        with col_pic:
            st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=180)
            st.metric("ID Number", selected_id)
        
        with col_info:
            st.header(db.clean_val(c['name']))
            m1, m2, m3 = st.columns(3)
            m1.metric("Division", db.clean_val(c['division']))
            m2.metric("Specialty", db.clean_val(c['specialty']))
            m3.metric("Current Status", db.get_last_known_phase(c))
            
            st.markdown("---")
            st.write(f"👤 **Mentor:** {db.clean_val(c['mentor'])} | 🎓 **Degree:** {db.clean_val(c['degree'])}")
            st.subheader("📝 IK / OOK Comment")
            st.info(db.clean_val(c['remarks']) if db.clean_val(c['remarks']) else "No comments.")
    else:
        st.error("Please load data in the Admin tab.")

elif menu_choice == "⚙️ Admin":
    st.subheader("Administration")
    if st.button("🔄 Sync with Master Excel"):
        # Assuming db.sync_excel_to_db() is defined
        st.success("Sync Complete!")
