import os
import sys
import streamlit as st

# Display a "loading" message while we import everything else
st.title("Google Workspace SSO Integration Tools")
loading_message = st.text("Loading application...")

try:
    import json
    import datetime
    import pandas as pd
    import logging
    from typing import Dict, List, Any, Optional
    import tempfile
    from dotenv import load_dotenv
    
    # Debug information
    print("Python version:", sys.version)
    print("Current working directory:", os.getcwd())
    print("Directory contents:", os.listdir())
    print("Environment variables:", {k: v for k, v in os.environ.items() if not k.startswith('AWS_')})
    
    # If running on Streamlit Cloud, use secrets
    if "DATABASE_URL" in st.secrets:
        os.environ["DATABASE_URL"] = st.secrets["DATABASE_URL"]
        
    # For other environment variables
    for key in ["GCP_PROJECT_ID", "GCP_REGION", "DOMAIN", "ADMIN_EMAIL", 
               "SERVICE_ACCOUNT_NAME", "SCIM_BRIDGE_IMAGE"]:
        if key in st.secrets:
            os.environ[key] = st.secrets[key]
    
    # Update loading message
    loading_message.text("Initializing database...")
    
    # Import database after setting environment variables
    try:
        from database import init_db, add_default_services
        
        # Initialize database
        try:
            init_db()
            add_default_services()
            print("Database initialization successful")
        except Exception as e:
            print(f"Database initialization error: {str(e)}")
            st.error(f"Database error: {str(e)}")
    except Exception as e:
        st.error(f"Failed to import database module: {str(e)}")
    
    # Update loading message
    loading_message.text("Loading application components...")
    
    # Try to import other components
    try:
        from email_verification_manager import EmailVerificationManager
        from email_list_manager import EmailListManager
        
        # Initialize managers
        verification_manager = EmailVerificationManager()
        list_manager = EmailListManager()
    except Exception as e:
        st.error(f"Failed to import application components: {str(e)}")
    
    # Remove loading message
    loading_message.empty()
    
    # Main application UI
    st.title("Google Workspace SSO Integration Tools")
    st.write("Welcome to the Google Workspace SSO Integration Tools. This application helps you set up SSO with Google Workspace.")
    
    # Simple UI as a fallback
    st.success("Application loaded successfully!")
    
    # Show system information (for debugging)
    if st.checkbox("Show System Information"):
        st.write("### System Information")
        st.write(f"Python version: {sys.version}")
        st.write(f"Current directory: {os.getcwd()}")
        st.write(f"Directory contents: {os.listdir()}")
    
except Exception as e:
    # If everything fails, at least show a meaningful error
    st.error(f"Application failed to start: {str(e)}")
    st.write("### Debug Information")
    st.write(f"Python version: {sys.version}")
    st.write(f"Current directory: {os.getcwd()}")
    import traceback
    st.code(traceback.format_exc()) 