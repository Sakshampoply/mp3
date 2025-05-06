import streamlit as st
from frontend.services.api_client import api_get

st.title("Candidate Dashboard")

tab1, tab2 = st.tabs(["View Jobs", "Upload Resume"])

with tab1:
    st.subheader("Available Jobs")
    jobs = api_get("/jobs?active_only=true", st.session_state.token)
    for job in jobs:
        st.write(f"### {job['title']}")
        st.write(f"**Skills:** {', '.join(job['skills_required'])}")
        st.write(job["description"])

with tab2:
    st.page_link("pages/resume_upload.py", label="Upload New Resume")
