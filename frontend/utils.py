import streamlit as st


def display_education(resume_data):
    """Display education section"""
    st.subheader("Education")
    education = resume_data.get("education", [])

    if not education:
        st.warning("No education information available")
        return

    for edu in education:
        with st.expander(edu.get("degree", "Unknown Degree")):
            st.write(f"**Institution:** {edu.get('institute', 'Not specified')}")
            st.write(f"**Years:** {edu.get('years', 'Not specified')}")


def display_experience(resume_data):
    """Display experience section"""
    st.subheader("Experience")
    experience = resume_data.get("experience", [])

    if not experience:
        st.warning("No experience information available")
        return

    for exp in experience:
        with st.expander(exp.get("title", "Unknown Position")):
            st.write(f"**Company:** {exp.get('company', 'Not specified')}")
            st.write(f"**Duration:** {exp.get('duration', 'Not specified')}")
            st.write(f"**Description:** {exp.get('description', '')}")
