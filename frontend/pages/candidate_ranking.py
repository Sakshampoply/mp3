import streamlit as st
from frontend.services.api_client import api_get

st.title("Rank Candidates by Job Relevance")

# Get jobs with error handling
jobs_response = api_get("/jobs", st.session_state.token)

if isinstance(jobs_response, list):
    # Valid job data case
    if len(jobs_response) == 0:
        st.warning("No jobs available")
        st.stop()

    job_titles = [job.get("title", "Untitled Position") for job in jobs_response]
    selected_index = st.selectbox(
        "Select Job", range(len(jobs_response)), format_func=lambda i: job_titles[i]
    )
    selected_job = jobs_response[selected_index]

elif isinstance(jobs_response, dict) and "error" in jobs_response:
    # API error case
    st.error(f"Failed to load jobs: {jobs_response['error']}")
    st.stop()
else:
    # Unexpected response format
    st.error("Unexpected response from server")
    st.stop()

if selected_job:
    ranked = api_get(
        f"/search/rank_candidates?job_id={selected_job['id']}", st.session_state.token
    )

    if isinstance(ranked, list):
        for candidate in ranked:
            st.subheader(f"Score: {candidate.get('score', 0):.2f}")
            st.write(
                f"**Email:** {candidate.get('candidate', {}).get('email', 'Unknown')}"
            )
            if candidate.get("matching_resume"):
                st.write(
                    "**Matching Skills:**",
                    ", ".join(candidate["matching_resume"].get("skills", [])),
                )
    else:
        st.error("Failed to load candidates ranking")
