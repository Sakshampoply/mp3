import streamlit as st
from services.api_client import api_get

st.title("Candidate Search")

skills = st.text_input("Enter skills (comma separated)")
if skills:
    candidates = api_get(f"/resumes/candidates?skills={skills}", st.session_state.token)

    for candidate in candidates:
        with st.expander(candidate.get("email", "Unknown Email")):
            # Handle resumes
            resumes = candidate.get("resumes", [])

            if resumes:
                first_resume = resumes[0]
                st.write(f"**Skills:** {', '.join(first_resume.get('skills', []))}")

                # Handle experience years
                experience = first_resume.get("experience_years", "Not specified")
                st.write(f"**Experience:** {experience} years")

                # Handle education
                education = first_resume.get("education", [])
                if education:
                    st.write("**Education:**")
                    for edu in education:
                        st.write(f"- {edu.get('degree', 'Unknown degree')}")
            else:
                st.warning("No resumes found for this candidate")
