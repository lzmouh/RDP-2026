import streamlit as st
import pandas as pd
import io
import database as db

# --- CONFIGURATION ---
st.set_page_config(page_title="EXPEC ARC RDP Portal", layout="wide")

# Initialize Database and handle Excel-to-DB migration on first run
db.init_db()

# Custom CSS to improve UI
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ EXPEC ARC RDP Management System")

# Helper function to clean "None" strings for display
def clean_display(val):
    if val is None or str(val).lower() in ["none", "nan", "null"]:
        return ""
    return str(val)

# --- NAVIGATION ---
tabs = st.tabs(["📊 Dashboard", "👤 Candidate Profiling", "🎯 Scoring Matrix", "⚙️ Administration"])

# --- TAB 1: DASHBOARD ---
with tabs[0]:
    st.subheader("Candidate Search & Overview")
    search = st.text_input("Search by Name or ID#", placeholder="Type to filter...")
    
    raw_df = db.get_all_candidates(search)
    
    # Clean DataFrame for UI display
    display_df = raw_df.copy()
    for col in display_df.columns:
        display_df[col] = display_df[col].apply(clean_display)
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)

# --- TAB 2: PROFILING ---
with tabs[1]:
    st.subheader("Edit Candidate Profile")
    all_cands = db.get_all_candidates()
    
    if not all_cands.empty:
        # Create a selectbox that shows Name + ID
        cand_list = all_cands.apply(lambda x: f"{x['candidate_id']} - {x['name']}", axis=1).tolist()
        choice = st.selectbox("Select Candidate", cand_list)
        selected_id = choice.split(" - ")[0]
        
        c_data = all_cands[all_cands["candidate_id"] == selected_id].iloc[0]
        
        with st.form("edit_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                name = st.text_input("Full Name", value=clean_display(c_data["name"]))
                div = st.text_input("Division", value=clean_display(c_data["division"]))
            with col2:
                spec = st.text_input("Specialty", value=clean_display(c_data["specialty"]))
                # Clean the phase value for the selectbox
                current_ph = clean_display(c_data["phase_2025"])
                ph_options = ["", "1", "2", "3"]
                ph_index = ph_options.index(current_ph) if current_ph in ph_options else 0
                phase = st.selectbox("Current Phase (2025)", ph_options, index=ph_index)
            with col3:
                degree = st.text_input("Degree (MS/PhD)", value=clean_display(c_data["degree"]))
                nat = st.text_input("Nationality", value=clean_display(c_data["nationality"]))
                
            remarks = st.text_area("Notes/Remarks", value=clean_display(c_data["remarks"]))
            
            if st.form_submit_button("💾 Update Record"):
                db.update_candidate((selected_id, name, div, spec, phase, remarks))
                st.success(f"Profile for {selected_id} updated successfully!")
                st.rerun()
    else:
        st.info("No candidates found. Please sync data in the Administration tab.")

# --- TAB 3: SCORING MATRIX ---
with tabs[2]:
    st.subheader("Performance & KPI Scoring")
    if not all_cands.empty:
        col_sel, col_empty = st.columns([1, 2])
        target_id = col_sel.selectbox("Select ID to Score", all_cands["candidate_id"], key="score_sel")
        
        col_view, col_input = st.columns([2, 1])
        
        with col_view:
            st.write("**Recent KPI Entries**")
            scores = db.get_candidate_scores(target_id)
            if not scores.empty:
                st.table(scores)
            else:
                st.caption("No scores recorded yet for this candidate.")
                
        with col_input:
            with st.container(border=True):
                st.write("**Add New Score**")
                category = st.selectbox("KPI Category", ["Technical Expertise", "Leadership", "Research", "Soft Skills"])
                score_val = st.number_input("Score (0-100)", 0, 100, 50)
                if st.button("Submit Score"):
                    db.add_score(target_id, category, score_val)
                    st.success("Score added!")
                    st.rerun()
    else:
        st.warning("Database is empty.")

# --- TAB 4: ADMINISTRATION ---
with tabs[3]:
    st.subheader("Data Management")
    
    c1, c2 = st.columns(2)
    with c1:
        st.write("### Excel Synchronization")
        st.info("This will overwrite existing info with data from 'RDP Master.xlsx'")
        if st.button("🔄 Sync with Master Excel"):
            db.sync_excel_to_db()
            st.success("Sync Complete!")
            st.rerun()
            
    with c2:
        st.write("### Export Records")
        st.write("Download the current database state as an Excel file.")
        
        # Prepare Export
        export_df = db.get_all_candidates()
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            export_df.to_excel(writer, index=False, sheet_name='RDP_Export')
        
        st.download_button(
            label="📥 Download current_db.xlsx",
            data=output.getvalue(),
            file_name="RDP_Database_Export.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

st.sidebar.markdown("---")
st.sidebar.caption(f"System Version: 2.1 | Data Source: {db.DB_PATH}")
