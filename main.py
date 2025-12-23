import streamlit as st
import pandas as pd
import io
import database as db

st.set_page_config(page_title="EXPEC ARC RDP Portal", layout="wide")
db.init_db()

# --- UTILITY FUNCTIONS ---
def clean_display(val):
    if val is None or str(val).lower() in ["none", "nan", "null"]:
        return ""
    return str(val).strip()

def get_latest_phase(r):
    """Checks 2025, then 2024, 2023, 2022 to find the most recent phase."""
    for year in ['phase_2025', 'phase_2024', 'phase_2023', 'phase_2022']:
        val = clean_display(r.get(year))
        if val != "":
            return val
    return "N/A"

# Initialize session state for navigation if it doesn't exist
if "selected_candidate_id" not in st.session_state:
    st.session_state.selected_candidate_id = None

# --- UI TABS ---
# We use a selectbox or sidebar for high-level navigation, 
# but "link" the dashboard to the profile tab.
menu = ["📊 Dashboard", "👤 Candidate Profile", "🎯 Scoring Matrix", "⚙️ Administration"]
choice = st.sidebar.selectbox("Navigation", menu)

# --- TAB: DASHBOARD ---
if choice == "📊 Dashboard":
    st.title("Candidate Search & Overview")
    st.info("💡 Select a row to view the full candidate profile.")
    
    search = st.text_input("Search by Name or ID#", placeholder="Type to filter...")
    raw_df = db.get_all_candidates(search)
    
    if not raw_df.empty:
        # Prepare a display version of the dataframe
        display_df = raw_df.copy()
        display_df['Current/Last Phase'] = display_df.apply(get_latest_phase, axis=1)
        
        # We only show relevant columns in the main table
        cols_to_show = ['candidate_id', 'name', 'division', 'specialty', 'mentor', 'Current/Last Phase']
        
        # Use st.dataframe with selection enabled
        event = st.dataframe(
            display_df[cols_to_show],
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single"
        )

        # LINKING LOGIC: If a user clicks a row, save the ID and tell them to go to Profile
        if len(event.selection.rows) > 0:
            selected_index = event.selection.rows[0]
            st.session_state.selected_candidate_id = display_df.iloc[selected_index]['candidate_id']
            st.success(f"Selected: {st.session_state.selected_candidate_id}. Click 'Candidate Profile' in the sidebar to view.")

# --- TAB: PROFILE ---
elif choice == "👤 Candidate Profile":
    st.title("Candidate Profile Details")
    all_cands = db.get_all_candidates()
    
    if not all_cands.empty:
        # Determine which ID to show (either from Dashboard click or Selectbox)
        default_idx = 0
        if st.session_state.selected_candidate_id:
            try:
                default_idx = all_cands.index[all_cands['candidate_id'] == st.session_state.selected_candidate_id].tolist()[0]
            except: default_idx = 0
            
        choice_id = st.selectbox("Select Candidate ID", all_cands["candidate_id"], index=default_idx)
        c = all_cands[all_cands["candidate_id"] == choice_id].iloc[0]

        # PROFILE LAYOUT
        col_photo, col_main = st.columns([1, 3])
        
        with col_photo:
            # Display Photo Placeholder
            st.image("https://cdn-icons-png.flaticon.com/512/149/149071.png", width=200)
            st.caption(f"ID: {c['candidate_id']}")
            
        with col_main:
            st.header(clean_display(c['name']))
            
            p1, p2, p3 = st.columns(3)
            p1.metric("Division", clean_display(c['division']))
            p2.metric("Specialty", clean_display(c['specialty']))
            
            # PHASE LOGIC: Report last known phase
            latest_phase = get_latest_phase(c)
            p3.metric("Current/Last Phase", latest_phase)

            st.divider()
            
            st.subheader("Professional Details")
            d1, d2 = st.columns(2)
            d1.write(f"**Mentor Name:** {clean_display(c['mentor'])}")
            d2.write(f"**Degree:** {clean_display(c['degree'])}")
            
            st.write("---")
            st.subheader("IK / OOK Comment")
            # Displaying remarks as the IK/OOK comment field
            remarks_val = clean_display(c['remarks'])
            if remarks_val:
                st.info(remarks_val)
            else:
                st.write("*No comments available.*")

# --- OTHER TABS (Simplified placeholders) ---
elif choice == "🎯 Scoring Matrix":
    st.title("Scoring Matrix")
    st.write("KPI Logic here...")

elif choice == "⚙️ Administration":
    st.title("Admin")
    if st.button("Sync with Master Excel"):
        db.sync_excel_to_db()
        st.success("Synced!")
