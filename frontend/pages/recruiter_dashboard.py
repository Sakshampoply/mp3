import streamlit as st

st.title("Recruiter Dashboard")

# Navigation buttons - removed kwargs parameter
cols = st.columns(4)
cols[0].page_link("pages/job_management.py", label="Manage Jobs")
cols[1].page_link("pages/candidate_search.py", label="Search Candidates")
cols[2].page_link("pages/candidate_ranking.py", label="Rank Candidates")

# New View Resume button with session state handling
if cols[3].button("View Resume"):
    st.session_state["show_resume_input"] = True

# Show resume ID input when needed
if st.session_state.get("show_resume_input"):
    resume_id = st.text_input("Enter Resume ID", key="resume_id_input")
    if st.button("Submit"):
        if resume_id and resume_id.isdigit():
            st.session_state["resume_id"] = resume_id
            st.switch_page("pages/resume_viewer.py")
        else:
            st.error("Please enter a valid numeric Resume ID")
