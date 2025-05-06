import streamlit as st
from frontend.services.api_client import api_delete, api_get, api_post, api_put


def create_job_form():
    with st.form("create_job"):
        title = st.text_input("Title")
        desc = st.text_area("Description")
        reqs = st.text_area("Requirements")
        submitted = st.form_submit_button("Create Job")
        if submitted:
            response = api_post(
                "/jobs",
                data={
                    "title": title,
                    "company": "",
                    "location": "",
                    "description": desc,
                    "requirements": reqs,
                },
                token=st.session_state.token,
            )
            if "id" in response:
                st.success("Job created!")
                st.rerun()
            else:
                st.error("Error creating job")


def manage_jobs():
    jobs = api_get("/jobs", st.session_state.token) or []
    for job in jobs:
        with st.expander(job.get("title", "Untitled Position")):
            with st.form(f"edit_job_{job.get('id')}"):
                title = st.text_input("Title", value=job.get("title", ""))
                desc = st.text_area("Description", value=job.get("description", ""))
                reqs = st.text_area("Requirements", value=job.get("requirements", ""))

                cols = st.columns(2)
                if cols[0].form_submit_button("Update"):
                    response = api_put(
                        f"/jobs/{job.get('id')}",
                        {
                            "title": title,
                            "description": desc,
                            "requirements": reqs,
                        },
                        st.session_state.token,
                    )
                    st.rerun()

                if cols[1].form_submit_button("Delete"):
                    api_delete(f"/jobs/{job.get('id')}", st.session_state.token)
                    st.rerun()


def main():
    st.title("Job Management")
    tab1, tab2 = st.tabs(["Create Job", "Manage Existing"])
    with tab1:
        create_job_form()
    with tab2:
        manage_jobs()


if __name__ == "__main__":
    main()
