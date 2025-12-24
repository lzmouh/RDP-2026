import streamlit as st
import pandas as pd
import database as db

# --- CONFIGURATION ---
st.set_page_config(page_title="RDP Portal", layout="wide")
db.init_db()

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
    return "N/A"

# Session State for navigation
if "active_id" not in st.session_state:
    st.session_state.active_id = None

# --- SIDEBAR MENU ---
with st.sidebar:
    st.title("RDP Navigation")
    menu_choice = st.radio(
        "Menu",
        ["📊 Dashboard", "👤 Candidate Profile", "⚙️ Administration"]
    )
    st.divider()
    if st.session_state.active_id:
        st.success(f"Selected: {st.session_state.active_id}")

# --- MODULES ---

if menu_choice == "📊 Dashboard":
    st.subheader("Candidate Directory")
    search = st.text_input("🔍 Search candidates...", "")
    df = db.get_all_candidates(search)
    
    if not df.empty:
        disp_df = df.copy()
        disp_df['Last Known Phase'] = disp_df.apply(get_last_known_phase, axis=1)
        cols = ['candidate_id', 'name', 'division', 'mentor', 'Last Known Phase']
        
        # VERSION-SAFE DATAFRAME
        try:
            # Try the modern interactive selection (Requires Streamlit 1.35+)
            event = st.dataframe(
                disp_df[cols],
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single"
            )
            
            if event.selection.rows:
                idx = event.selection.rows[0]
                st.session_state.active_id = disp_df.iloc[idx]['candidate_id']
                st.toast(f"Selected {st.session_state.active_id}")

        except Exception:
            # Fallback for older Streamlit versions
            st.dataframe(disp_df[cols], use_container_width=True, hide_index=True)
            st.info("To view a profile, select the ID in the 'Candidate Profile' tab.")

elif menu_choice == "👤 Candidate Profile":
    st.subheader("Candidate Detail View")
    all_cands = db.get_all_candidates()
    
    if not all_cands.empty:
        # Get index for selectbox
        try:
            default_idx = all_cands.index[all_cands['candidate_id'] == st.session_state.active_id].tolist()[0]
        except:
            default_idx = 0
            
        selected_id = st.selectbox("Select Candidate ID:", all_cands['candidate_id'], index=default_idx)
        c = all_cands[all_cands['candidate_id'] == selected_id].iloc[0]
        
        # Profile UI
        col_pic, col_info = st.columns([1, 3])
        with col_pic:
            # Placeholder Image
            st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=180)
            st.metric("ID#", selected_id)

        with col_info:
            st.header(clean_val(c['name']))
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
                st.caption("No comments recorded.")
    else:
        st.error("No data available.")

elif menu_choice == "⚙️ Administration":
    st.subheader("System Administration")
    if st.button("🔄 Reload from RDP Master.xlsx"):
        db.sync_excel_to_db()
        st.success("Database updated successfully!")
