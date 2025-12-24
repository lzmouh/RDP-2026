import streamlit as st


def about_page():
    st.title("RDP Scoring Framework & KPIs")

    st.header("Achievement Categories")
    st.markdown("""
    **Publications** – Journals, conferences, reports  
    **Innovation** – Patents, disclosures, Mad-Twix  
    **Projects & Deployment** – Research leadership and field deployment  
    **Knowledge Sharing** – Teaching, talks, mentoring  
    **Professional Leadership** – Committees, editorial roles
    """)

    st.header("Weight Factors")
    st.markdown("""
    - Patent > Journal > Conference > Report  
    - Lead author / inventor ×1.5  
    - Co-author ×1.0
    """)

    st.header("Phase Thresholds")
    st.table({
        "Phase": ["Phase 1", "Phase 2", "Phase 3", "Graduation"],
        "Engineering": [60, 120, 200, 250],
        "Geoscience": [55, 110, 190, 240],
        "Data Science": [50, 100, 180, 230]
    })

    st.header("Graduation Project")
    st.markdown("""
    - Novelty & originality: 20 pts  
    - Technology value & ROI: 30 pts  
    - Mandatory for graduation
    """)
