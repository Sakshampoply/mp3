import os

import streamlit as st


def load_css():
    css_path = os.path.join(os.path.dirname(__file__), "styles.css")  # Fixed line
    with open(css_path) as f:
        css = f"<style>{f.read()}</style>"
    st.markdown(css, unsafe_allow_html=True)
