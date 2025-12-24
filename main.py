import streamlit as st
from database import SessionLocal, Candidate
import uuid

st.set_page_config(page_title="RDP Management", layout="wide")

pages = {
    "Candidates": "profile",
    "Analytics": "analytics",
    "About / Scoring": "about"
}

st.sidebar.title("RDP Navigation")
selection = st.sidebar.radio("Go to", list(pages.keys()))

if selection == "Candidates":
    from profile import profile_page
    profile_page()
elif selection == "Analytics":
    from analytics import analytics_page
    analytics_page()
elif selection == "About / Scoring":
    from about import about_page
    about_page()
