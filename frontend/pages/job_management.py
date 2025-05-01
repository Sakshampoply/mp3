import streamlit as st
from services.api_client import api_delete, api_get, api_post, api_put

st.title("Job Management")

tab1, tab2 = st.tabs(["Create Job", "Manage Existing"])

with tab1:
    with st.form("create_job"):
        title = st.text_input("Title")
        desc = st.text_area("Description")
        reqs = st.text_area("Requirements")
        if st.form_submit_button("Create Job"):
            response = api_post(
                "/jobs",
                {"title": title, "description": desc, "requirements": reqs},
                st.session_state.token,
            )
            st.success("Job created!") if "id" in response else st.error("Error")

with tab2:
    jobs = api_get("/jobs", st.session_state.token)
    for job in jobs:
        with st.expander(job["title"]):
            with st.form(f"edit_job_{job['id']}"):
                title = st.text_input("Title", value=job["title"])
                desc = st.text_area("Description", value=job["description"])
                reqs = st.text_area("Requirements", value=job["requirements"])

                cols = st.columns(2)
                if cols[0].form_submit_button("Update"):
                    response = api_put(
                        f"/jobs/{job['id']}",
                        {"title": title, "description": desc, "requirements": reqs},
                        st.session_state.token,
                    )
                    st.rerun()

                if cols[1].form_submit_button("Delete"):
                    api_delete(f"/jobs/{job['id']}", st.session_state.token)
                    st.rerun()
