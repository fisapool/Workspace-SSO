import streamlit as st
import os
import sys

st.title("Minimal Test App")
st.write("This is a minimal test to debug deployment issues")
st.write(f"Python version: {sys.version}")
st.write(f"Current directory: {os.getcwd()}")
st.write(f"Directory contents: {os.listdir()}")

# This will help identify issues with your secrets
if st.secrets:
    st.write("Secrets are available")
else:
    st.write("No secrets found")

# Success message
st.success("If you can see this, the minimal app works!") 