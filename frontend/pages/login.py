import streamlit as st
from frontend.services.auth import login

st.title("Login")

email = st.text_input("Email")
password = st.text_input("Password", type="password")

col1, col2 = st.columns([1, 3])
with col1:
    if st.button("Login"):
        if login(email, password):
            st.success("Logged in successfully!")
            st.rerun()
        else:
            st.error("Invalid credentials")

with col2:
    st.page_link("pages/register.py", label="Create new account")
