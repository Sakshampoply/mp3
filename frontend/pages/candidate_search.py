import streamlit as st
from frontend.services.api_client import api_get

st.title("Candidate Search")

skills = st.text_input("Enter skills (comma separated)")
if skills:
    candidates = api_get(f"/search/candidates?skills={skills}", st.session_state.token)

    if isinstance(candidates, dict) and "error" in candidates:
        st.error(f"Error: {candidates['error']}")
    elif isinstance(candidates, list):
        for candidate in candidates:
            # Safely handle candidate data
            email = candidate.get("email", "Unknown Email")
            with st.expander(email):
                resumes = candidate.get("resumes", [])
                if resumes:
                    first_resume = resumes[0]
                    st.write(f"**Skills:** {', '.join(first_resume.get('skills', []))}")
                    st.write(
                        f"**Experience:** {first_resume.get('experience_years', 'Not specified')}"
                    )
                else:
                    st.warning("No resume data available")
    else:
        st.warning("No candidates found")
