import os
import sys
import streamlit as st

# Print debug info to logs
print("Starting simple_app.py")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Files: {os.listdir()}")

# Set page configuration
st.set_page_config(
    page_title="Google Workspace SSO Integration",
    page_icon="🔑",
    layout="wide"
)

st.title("Google Workspace SSO Integration")

# If we have secrets, use them
try:
    # Show available secrets keys (not values)
    if hasattr(st, "secrets") and st.secrets:
        print("Secrets are available")
        for key in st.secrets:
            print(f"Secret key found: {key}")
            if key != "DATABASE_URL":  # Don't set DATABASE_URL from secrets yet
                os.environ[key] = st.secrets[key]
    else:
        print("No secrets found")
        st.warning("No configuration secrets found. Some features may not work.")
except Exception as e:
    print(f"Error processing secrets: {str(e)}")
    st.error(f"Configuration error: {str(e)}")

# Create a simple UI
tab1, tab2 = st.tabs(["Setup", "Information"])

with tab1:
    st.header("Setup Google Workspace SSO")
    
    with st.form("setup_form"):
        domain = st.text_input("Domain Name")
        admin_email = st.text_input("Admin Email")
        project_id = st.text_input("Google Cloud Project ID")
        
        submit = st.form_submit_button("Save Configuration")
        
        if submit:
            st.success("Configuration saved!")
            # In a real app, you would save these values

with tab2:
    st.header("System Information")
    st.write(f"Python version: {sys.version}")
    st.write(f"Current directory: {os.getcwd()}")
    
    # Show directory contents
    files_dirs = os.listdir()
    st.write("### Directory Contents:")
    for item in files_dirs:
        if os.path.isdir(item):
            st.write(f"📁 {item}/")
        else:
            st.write(f"📄 {item}") 