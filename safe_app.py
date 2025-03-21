import streamlit as st
import sys
import os

# Basic UI
st.title("Failsafe App")
st.write("This is a minimal version that should always run")

# Display system info
st.write("### System Information")
st.write(f"Python version: {sys.version}")
st.write(f"Current directory: {os.getcwd()}")

try:
    # Try to list directory contents
    st.write("### Directory Contents")
    st.write(os.listdir())
except Exception as e:
    st.error(f"Error listing directory: {str(e)}")

try:
    # Try to display secrets
    st.write("### Secrets")
    if hasattr(st, "secrets") and st.secrets:
        st.write("Secrets are available")
        # Safely show keys without values
        st.write(f"Secret keys: {list(st.secrets.keys())}")
    else:
        st.write("No secrets found")
except Exception as e:
    st.error(f"Error checking secrets: {str(e)}")

# Success message
st.success("Basic app loaded successfully!") 