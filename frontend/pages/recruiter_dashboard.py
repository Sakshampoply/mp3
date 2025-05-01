import streamlit as st

st.title("Recruiter Dashboard")

cols = st.columns(3)
cols[0].page_link("pages/job_management.py", label="Manage Jobs")
cols[1].page_link("pages/candidate_search.py", label="Search Candidates")
cols[2].page_link("pages/candidate_ranking.py", label="Rank Candidates")
