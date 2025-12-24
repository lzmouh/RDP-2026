import streamlit as st
import pandas as pd
import plotly.express as px
from database import SessionLocal, Candidate


def analytics_page():
    db = SessionLocal()
    candidates = db.query(Candidate).all()

    df = pd.DataFrame([{
        "Phase": c.phase,
        "Division": c.division
    } for c in candidates])

    st.title("RDP Analytics")

    if df.empty:
        st.info("No data available")
        return

    st.subheader("Candidates vs Phase")
    st.plotly_chart(px.bar(df, x="Phase"))

    st.subheader("Candidates vs Division")
    st.plotly_chart(px.bar(df, x="Division"))

    st.subheader("Interactive Filter")
    division = st.selectbox("Division", ["All"] + df.Division.unique().tolist())
    phase = st.selectbox("Phase", ["All"] + df.Phase.unique().tolist())

    filtered = df
    if division != "All":
        filtered = filtered[filtered.Division == division]
    if phase != "All":
        filtered = filtered[filtered.Phase == phase]

    st.dataframe(filtered)
