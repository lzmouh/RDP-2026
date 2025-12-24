import streamlit as st
import pandas as pd
import database as db

# --- INITIALIZATION ---
st.set_page_config(page_title="RDP Portal", layout="wide")
db.init_db()

if "active_id" not in st.session_state:
    st.session_state.active_id = None
if "menu_selection" not in st.session_state:
    st.session_state.menu_selection = "📊 Dashboard"

# --- SIDEBAR MENU ---
with st.sidebar:
    st.title("RDP Navigation")
    # This is the fixed vertical menu
    choice = st.radio(
        "Menu", 
        ["📊 Dashboard", "👤 Profile", "⚙️ Admin"],
        index=["📊 Dashboard", "👤 Profile", "⚙️ Admin"].index(st.session_state.menu_selection)
    )
    st.session_state.menu_selection = choice

# --- DASHBOARD ---
if choice == "📊 Dashboard":
    st.header("Candidate Directory")
    search = st.text_input("🔍 Search candidates...", placeholder="Name or ID#")
    
    df = db.get_all_candidates(search)
    if not df.empty:
        # 1. Logic: Last Known Phase
        df['Current Phase'] = df.apply(db.get_last_known_phase, axis=1)
        
        # 2. Add Index and Visual Arrow
        display_df = df[['candidate_id', 'name', 'specialty', 'division', 'mentor', 'Current Phase']].copy()
        display_df.insert(0, 'No.', range(1, len(display_df) + 1))
        display_df.insert(1, 'Profile', '➡️ View') # Visual arrow button

        st.info("💡 Click on any row to view the full candidate profile.")
        
        # 3. Native Selection Table
        event = st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single"
        )

        # 4. Same-Tab Navigation Logic
        if len(event.selection.rows) > 0:
            selected_idx = event.selection.rows[0]
            st.session_state.active_id = display_df.iloc[selected_idx]['candidate_id']
            st.session_state.menu_selection = "👤 Profile"
            st.rerun()
    else:
        st.warning("No data found.")

# --- PROFILE ---
elif choice == "👤 Profile":
    st.header("Candidate Profile")
    all_cands = db.get_all_candidates()
    
    if not all_cands.empty:
        # Link from Dashboard selection
        try:
            d_idx = all_cands.index[all_cands['candidate_id'] == st.session_state.active_id].tolist()[0]
        except:
            d_idx = 0
            
        selected_id = st.selectbox("Switch Candidate:", all_cands['candidate_id'], index=d_idx)
        c = all_cands[all_cands['candidate_id'] == selected_id].iloc[0]
        st.session_state.active_id = selected_id

        # Profile Layout
        col_photo, col_main = st.columns([1, 3])
        
        with col_photo:
            # Photo Placeholder
            st.image("https://cdn-icons-png.flaticon.com/512/149/149071.png", width=200)
            st.metric("Candidate ID", selected_id)

        with col_main:
            st.subheader(db.clean_val(c['name']))
            
            # Row 1: Key Metrics
            m1, m2, m3 = st.columns(3)
            m1.metric("Division", db.clean_val(c['division']))
            m2.metric("Specialty", db.clean_val(c['specialty']))
            m3.metric("Last Phase Recorded", db.get_last_known_phase(c))

            st.divider()
            
            # Row 2: Personnel Details
            d1, d2 = st.columns(2)
            d1.write(f"👤 **Mentor:** {db.clean_val(c['mentor'])}")
            d2.write(f"🎓 **Degree:** {db.clean_val(c['degree'])}")
            
            # Row 3: IK/OOK Comments
            st.write("---")
            st.write("### 📝 IK / OOK Comment")
            comment = db.clean_val(c['remarks'])
            if comment:
                st.info(comment)
            else:
                st.caption("No comments available for this candidate.")

# --- ADMIN ---
elif choice == "⚙️ Admin":
    st.header("System Admin")
    if st.button("🔄 Sync with Excel Database"):
        db.sync_data()
        st.success("Database synchronized successfully!")
