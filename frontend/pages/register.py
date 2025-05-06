import streamlit as st
from frontend.services.auth import register

st.title("Register")

email = st.text_input("Email")
password = st.text_input("Password", type="password")
role = st.selectbox("Role", ["candidate", "recruiter"])

if st.button("Register"):
    if register(email, password, role):
        st.success("Registration successful! Please login")
        st.switch_page("pages/login.py")
    else:
        st.error("Registration failed")
