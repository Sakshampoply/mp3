import streamlit as st
from frontend.styles.load_css import load_css

load_css()


def main():
    st.sidebar.title("Resume Screener")

    # Initialize session state
    if "token" not in st.session_state:
        st.session_state.token = None
    if "user_role" not in st.session_state:
        st.session_state.user_role = None

    if st.session_state.token:
        if st.session_state.user_role == "candidate":
            st.switch_page("pages/candidate_dashboard.py")
        else:
            st.switch_page("pages/recruiter_dashboard.py")
    else:
        st.switch_page("pages/login.py")


if __name__ == "__main__":
    main()
