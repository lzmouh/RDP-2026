import streamlit as st
import pandas as pd
import database as db
import urllib.parse

# --- SETUP ---
st.set_page_config(page_title="RDP Management System", layout="wide")
db.init_db()

# --- URL PARAMETER & SESSION STATE LOGIC ---
# This detects if a Candidate ID was clicked in the Dashboard
query_params = st.query_params

if "id" in query_params:
    clicked_id = query_params["id"]
    # Update Session State
    st.session_state.active_id = str(clicked_id)
    st.session_state.menu_index = 1  # Switch to Profile Tab
    # Clear parameters to prevent infinite loops/reloads
    st.query_params.clear()

if "active_id" not in st.session_state:
    st.session_state.active_id = None
if "menu_index" not in st.session_state:
    st.session_state.menu_index = 0

# --- HELPERS ---
def clean_val(val):
    if pd.isna(val) or str(val).lower() in ["none", "nan", ""]:
        return ""
    return str(val).split('.')[0] if isinstance(val, float) else str(val).strip()

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
        index=st.session_state.menu_index
    )
    # Update index if user clicks sidebar manually
    menu_map = {"📊 Dashboard": 0, "👤 Candidate Profile": 1, "⚙️ Administration": 2}
    st.session_state.menu_index = menu_map[menu_choice]

# --- MODULES ---

if menu_choice == "📊 Dashboard":
    st.subheader("Candidate Search & Dashboard")
    
    search = st.text_input("🔍 Filter by Name, ID, Specialty, or Mentor...", "")
    df = db.get_all_candidates(search)
    
    if not df.empty:
        # Calculate Logic
        df['Last Known Phase'] = df.apply(get_last_known_phase, axis=1)
        
        # Prepare Display Data
        display_df = df[['candidate_id', 'name', 'specialty', 'division', 'mentor', 'Last Known Phase']].copy()
        display_df.insert(0, 'No.', range(1, len(display_df) + 1))
        
        # --- HTML LINK LOGIC (Fixes Same Page Issue) ---
        # We create a custom HTML table because st.dataframe's LinkColumn always opens a new tab.
        def make_clickable_id(cid):
            # target='_self' ensures it stays in the same tab
            return f'<a href="/?id={cid}" target="_self" style="color: #007bff; text-decoration: none; font-weight: bold;">{cid}</a>'

        display_df['candidate_id'] = display_df['candidate_id'].apply(make_clickable_id)

        # Style the table
        html_table = display_df.to_html(escape=False, index=False, classes='table table-hover')
        
        # Standard CSS to make the HTML table look like a modern dashboard
        st.markdown("""
            <style>
            table { width: 100%; border-collapse: collapse; margin: 10px 0; font-family: sans-serif; }
            th { background-color: #f8f9fa; color: #333; text-align: left; padding: 12px; border-bottom: 2px solid #dee2e6; }
            td { padding: 12px; border-bottom: 1px solid #dee2e6; }
            tr:hover { background-color: #f1f1f1; }
            </style>
        """, unsafe_allow_html=True)
        
        st.write(html_table, unsafe_allow_html=True)
        st.caption("Tip: Click any **Candidate ID** to jump directly to their profile.")
    else:
        st.warning("No data found. Sync via Administration.")

elif menu_choice == "👤 Candidate Profile":
    st.subheader("Candidate Detailed Profile")
    all_cands = db.get_all_candidates()
    
    if not all_cands.empty:
        # Determine which ID to show based on Dashboard selection
        try:
            d_idx = all_cands.index[all_cands['candidate_id'] == st.session_state.active_id].tolist()[0]
        except:
            d_idx = 0
            
        selected_id = st.selectbox("Select Candidate to View:", all_cands['candidate_id'], index=d_idx)
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
            m3.metric("Current Status", get_last_known_phase(c))

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
                st.caption("No comments available for this candidate.")
    else:
        st.error("Please load data in the Admin tab first.")

elif menu_choice == "⚙️ Administration":
    st.subheader("System Administration")
    if st.button("🔄 Sync with RDP Master.xlsx"):
        db.sync_excel_to_db()
        st.success("Database synchronized successfully!")
        st.rerun()
