import streamlit as st
from frontend.services.api_client import api_get
from frontend.utils import display_education, display_experience


def display_resume_details(resume_data):
    """Display formatted resume data"""
    st.header(resume_data.get("candidate", {}).get("email", "Unknown Candidate"))

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Contact Information")
        st.write(f"**Phone:** {resume_data.get('phone', 'Not provided')}")

    with col2:
        st.subheader("Summary")
        st.write(resume_data.get("summary", "No summary available"))

    st.subheader("Skills")
    st.write(", ".join(resume_data.get("skills", [])) or "No skills listed")

    display_experience(resume_data)
    display_education(resume_data)


def main():
    st.title("Resume Viewer")

    if "token" not in st.session_state:
        st.error("Please login first")
        st.stop()

    # Check for resume ID in session state
    if "resume_id" not in st.session_state:
        with st.form("resume_lookup"):
            st.subheader("Enter Resume Details")
            resume_id = st.text_input("Resume ID", key="resume_input")

            if st.form_submit_button("View Resume"):
                if resume_id and resume_id.isdigit():
                    st.session_state["resume_id"] = resume_id
                    st.rerun()
                else:
                    st.error("Please enter a valid numeric Resume ID")
        return

    # Fetch and display resume
    response = api_get(
        f"/resumes/{st.session_state['resume_id']}", st.session_state.token
    )

    if isinstance(response, dict) and "error" in response:
        st.error(f"Error loading resume: {response['error']}")
    else:
        display_resume_details(response)

    # Navigation buttons
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Dashboard"):
            st.switch_page("pages/recruiter_dashboard.py")
    with col2:
        if st.button("🔍 View Another Resume"):
            st.session_state.pop("resume_id", None)
            st.rerun()


if __name__ == "__main__":
    main()
