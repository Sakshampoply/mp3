import time

import streamlit as st
from services.api_client import api_get, api_post

st.title("Upload Resume")

file = st.file_uploader("Choose a resume (PDF or DOCX)", type=["pdf", "docx"])

if file and st.button("Upload"):
    # Create proper multipart form data
    files = {"file": (file.name, file.getvalue(), file.type)}

    response = api_post("/resumes/upload", files=files, token=st.session_state.token)

    if "task_id" in response:
        st.success("Resume uploaded! Processing...")
        with st.status("Checking status"):
            while True:
                status = api_get(
                    f"/resumes/upload/status/{response['task_id']}",
                    st.session_state.token,
                )
                if status.get("processed"):
                    st.success("Processing complete!")
                    break
                time.sleep(2)
    else:
        st.error(f"Upload failed: {response.get('error', 'Unknown error')}")
