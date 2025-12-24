import streamlit as st
import pandas as pd
from database import SessionLocal, Candidate
import uuid


def profile_page():
    db = SessionLocal()
    st.title("RDP Candidates")

    candidates = db.query(Candidate).all()
    data = [{
        "ID": c.id,
        "Name": c.name,
        "Division": c.division,
        "Mentor": c.mentor,
        "Specialty": c.specialty,
        "Phase": c.phase,
        "Score": c.score
    } for c in candidates]

    df = pd.DataFrame(data)
    st.dataframe(df)

    st.subheader("Add / Update Candidate")
    with st.form("candidate_form"):
        name = st.text_input("Name")
        division = st.text_input("Division")
        mentor = st.text_input("Mentor")
        specialty = st.text_input("Specialty")
        phase = st.selectbox("Phase", ["Phase 1", "Phase 2", "Phase 3", "Graduation"])
        score = st.number_input("Current Score", min_value=0)
        comments = st.text_area("Comments")

        submit = st.form_submit_button("Save")
        if submit:
            c = Candidate(
                id=str(uuid.uuid4())[:8],
                name=name,
                division=division,
                mentor=mentor,
                specialty=specialty,
                phase=phase,
                score=score,
                comments=comments
            )
            db.add(c)
            db.commit()
            st.success("Candidate saved")
