import streamlit as st
import os
import sys

st.title("Streamlit Test App")

st.write("### System Information")
st.write(f"Python version: {sys.version}")
st.write(f"Current directory: {os.getcwd()}")
st.write(f"Directory contents: {os.listdir()}")

st.write("### Environment Variables")
env_vars = {k: v for k, v in os.environ.items() if not k.startswith('AWS_')}
st.write(env_vars)

st.success("Test app is running successfully!") 