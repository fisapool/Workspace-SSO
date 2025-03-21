import streamlit as st
import sys
import os
import time

# Print info to logs immediately
print("Starting cloud_app.py")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Files: {os.listdir()}")

# Basic Streamlit UI
st.set_page_config(
    page_title="Google Workspace Integration",
    page_icon="🔑",
    layout="wide"
)

st.title("Google Workspace SSO Integration")
st.write("Simple version for Streamlit Cloud")

# Display time to show the app is running
st.write(f"App started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

# Create tabs
tab1, tab2, tab3 = st.tabs(["Setup", "Configuration", "Testing"])

with tab1:
    st.header("Setup")
    st.write("This tab would help you set up Google Workspace integration.")
    
    # Simple form
    with st.form("setup_form"):
        domain = st.text_input("Domain")
        admin_email = st.text_input("Admin Email")
        project_id = st.text_input("GCP Project ID")
        submit = st.form_submit_button("Save")
        
        if submit:
            st.success("Configuration saved!")

with tab2:
    st.header("Configuration")
    st.write("This tab would show configuration options.")
    
    # Sample configuration display
    st.json({
        "domain": "example.com",
        "admin_email": "admin@example.com",
        "project_id": "example-project",
        "region": "us-central1"
    })

with tab3:
    st.header("Testing")
    st.write("This tab would allow testing the integration.")
    
    if st.button("Run Test"):
        with st.spinner("Testing connection..."):
            time.sleep(2)  # Simulate work
            st.success("Test completed successfully!")

# Show technical information
with st.expander("Technical Information"):
    st.write(f"Python version: {sys.version}")
    st.write(f"Current directory: {os.getcwd()}")
    st.write(f"Available files: {os.listdir()}") 