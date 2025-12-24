import streamlit as st
import pandas as pd
import database as db

# --- SETUP ---
st.set_page_config(page_title="RDP Management System", layout="wide")
db.init_db()

# --- CSS FOR MODERN TABLE ---
# We inject this at the top so it applies to the whole app
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');

    .modern-table-container {
        font-family: 'Inter', sans-serif;
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }

    .modern-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        margin: 10px 0;
        font-size: 15px; /* Adjust font size here */
    }

    .modern-table th {
        background-color: #F9FAFB;
        color: #4B5563;
        font-weight: 600;
        text-align: left;
        padding: 14px 16px;
        border-bottom: 1px solid #E5E7EB;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-size: 13px;
    }

    .modern-table td {
        padding: 16px;
        border-bottom: 1px solid #F3F4F6;
        color: #1F2937;
        line-height: 1.5;
    }

    .modern-table tr:hover {
        background-color: #FBFBFE;
    }

    .candidate-link {
        color: #2563EB;
        text-decoration: none;
        font-weight: 600;
        padding: 4px 8px;
        border-radius: 4px;
        transition: background-color 0.2s;
    }

    .candidate-link:hover {
        background-color: #DBEAFE;
        text-decoration: underline;
    }

    .phase-badge {
        background-color: #E0F2FE;
        color: #0369A1;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 500;
    }
    </style>
""", unsafe_allow_html=True)

# --- NAVIGATION LOGIC ---
query_params = st.query_params
if "id" in query_params:
    st.session_state.active_id = str(query_params["id"])
    st.session_state.menu_index = 1
    st.query_params.clear()

if "active_id" not in st.session_state: st.session_state.active_id = None
if "menu_index" not in st.session_state: st.session_state.menu_index = 0

# --- SIDEBAR ---
with st.sidebar:
    st.title("RDP Portal")
    menu_choice = st.radio("Menu", ["📊 Dashboard", "👤 Candidate Profile", "⚙️ Administration"], index=st.session_state.menu_index)
    st.session_state.menu_index = ["📊 Dashboard", "👤 Candidate Profile", "⚙️ Administration"].index(menu_choice)

# --- MODULES ---

if menu_choice == "📊 Dashboard":
    st.subheader("Candidate Search & Dashboard")
    
    search = st.text_input("🔍 Filter records...", placeholder="Search name, ID, or mentor")
    df = db.get_all_candidates(search)
    
    if not df.empty:
        # Prepare Data
        df['Last Known Phase'] = df.apply(lambda r: db.get_last_known_phase(r), axis=1) # Ensure this helper is in db
        
        display_df = df[['candidate_id', 'name', 'specialty', 'division', 'mentor', 'Last Known Phase']].copy()
        display_df.insert(0, 'No.', range(1, len(display_df) + 1))
        
        # HTML Rendering with Modern Classes
        table_html = '<div class="modern-table-container"><table class="modern-table"><thead><tr>'
        for col in display_df.columns:
            table_html += f'<th>{col.replace("_", " ")}</th>'
        table_html += '</tr></thead><tbody>'

        for _, row in display_df.iterrows():
            table_html += '<tr>'
            table_html += f'<td>{row["No."]}</td>'
            # Clickable ID with _self target
            table_html += f'<td><a href="/?id={row["candidate_id"]}" target="_self" class="candidate-link">{row["candidate_id"]}</a></td>'
            table_html += f'<td>{row["name"]}</td>'
            table_html += f'<td>{row["specialty"]}</td>'
            table_html += f'<td>{row["division"]}</td>'
            table_html += f'<td>{row["mentor"]}</td>'
            # Phase inside a badge
            table_html += f'<td><span class="phase-badge">{row["Last Known Phase"]}</span></td>'
            table_html += '</tr>'
        
        table_html += '</tbody></table></div>'
        
        st.write(table_html, unsafe_allow_html=True)
    else:
        st.warning("No data found.")
        
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
