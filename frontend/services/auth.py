import streamlit as st
from services.api_client import api_get, api_post


def login(email, password):
    response = api_post("/auth/login", {"email": email, "password": password})
    if "access_token" in response:
        st.session_state.token = response["access_token"]
        user_info = get_current_user()
        if user_info:
            st.session_state.user_role = user_info.get("role")
            return True
    return False


def register(email, password, role):
    response = api_post(
        "/auth/register", {"email": email, "password": password, "role": role}
    )
    return "message" in response


def get_current_user():
    response = api_get("/auth/me", st.session_state.token)
    return response if not "error" in response else None


def logout():
    st.session_state.token = None
    st.session_state.user_role = None
