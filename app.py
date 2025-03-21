"""
Email Verification System Dashboard

A Streamlit application for email verification and list management using multiple
verification services.
"""
import os
import json
import datetime
import pandas as pd
import streamlit as st
import logging
import sys
from typing import Dict, List, Any, Optional
import tempfile

# Try to import dotenv, but don't fail if it's not available
try:
    from dotenv import load_dotenv
    # Try to load from .env file (for local development)
    load_dotenv(os.path.join('config', '.env'))
except ImportError:
    # Define a dummy function if the module is not available
    def load_dotenv(*args, **kwargs):
        print("dotenv module not available, skipping .env file loading")
        pass

from database import init_db, add_default_services
from email_verification_manager import EmailVerificationManager
from email_list_manager import EmailListManager

# Debug information
print("Python version:", sys.version)
print("Current working directory:", os.getcwd())
print("Directory contents:", os.listdir())
print("Environment variables:", {k: v for k, v in os.environ.items() if not k.startswith('AWS_')})

# If running on Streamlit Cloud, use secrets
if not os.getenv("DATABASE_URL") and "DATABASE_URL" in st.secrets:
    os.environ["DATABASE_URL"] = st.secrets["DATABASE_URL"]
    
# For other environment variables
for key in ["GCP_PROJECT_ID", "GCP_REGION", "DOMAIN", "ADMIN_EMAIL", 
           "SERVICE_ACCOUNT_NAME", "SCIM_BRIDGE_IMAGE"]:
    if not os.getenv(key) and key in st.secrets:
        os.environ[key] = st.secrets[key]

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialize database
try:
    init_db()
    add_default_services()
    print("Database initialization successful")
except Exception as e:
    print(f"Database initialization error: {str(e)}")
    st.error(f"Database error: {str(e)}")

# Initialize managers
verification_manager = EmailVerificationManager()
list_manager = EmailListManager()

# Set page configuration
st.set_page_config(
    page_title="Email Verification System",
    page_icon="✉️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define session state initialization
if 'api_keys_configured' not in st.session_state:
    st.session_state.api_keys_configured = {}
    
    # Check which services have API keys configured
    for service_name in verification_manager.services.keys():
        service = verification_manager.services[service_name]
        if hasattr(service, 'api_key') and service.api_key:
            st.session_state.api_keys_configured[service_name] = True
        else:
            st.session_state.api_keys_configured[service_name] = False

# Functions
def save_api_key(service_name, api_key):
    """Save API key to environment and update session state."""
    os.environ[f"{service_name.upper()}_API_KEY"] = api_key
    
    # Update the service instance with the new API key
    verification_manager.services[service_name.lower()].api_key = api_key
    st.session_state.api_keys_configured[service_name.lower()] = True
    
    st.success(f"{service_name} API key saved successfully!")

def verify_single_email(email, service_name=None):
    """Verify a single email address."""
    with st.spinner(f"Verifying {email}..."):
        result = verification_manager.verify_email(email, service_name)
    return result

def verify_bulk_emails(emails, service_name=None):
    """Verify multiple email addresses."""
    with st.spinner(f"Verifying {len(emails)} emails..."):
        results = verification_manager.bulk_verify(emails, service_name)
    return results

def display_verification_result(result):
    """Display the result of an email verification."""
    if 'error' in result:
        st.error(f"Error: {result['error']}")
        return
    
    email = result.get('email', 'Unknown')
    is_valid = result.get('is_valid')
    score = result.get('score')
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Email")
        st.write(email)
    
    with col2:
        st.subheader("Validity")
        if is_valid is True:
            st.success("Valid ✓")
        elif is_valid is False:
            st.error("Invalid ✗")
        else:
            st.warning("Unknown ?")
    
    with col3:
        st.subheader("Score")
        if score is not None:
            st.progress(float(score))
            st.write(f"{score:.2f}/1.00")
        else:
            st.write("N/A")
    
    # If we have detailed results from multiple services
    if 'results' in result and isinstance(result['results'], dict):
        st.subheader("Results by Service")
        
        for service_name, service_result in result['results'].items():
            with st.expander(f"{service_name.capitalize()} Result"):
                if 'error' in service_result:
                    st.error(f"Error: {service_result['error']}")
                else:
                    cols = st.columns(3)
                    with cols[0]:
                        st.write("**Validity:**")
                        validity = service_result.get('is_valid')
                        if validity is True:
                            st.success("Valid ✓")
                        elif validity is False:
                            st.error("Invalid ✗")
                        else:
                            st.warning("Unknown ?")
                    
                    with cols[1]:
                        st.write("**Score:**")
                        srv_score = service_result.get('score')
                        if srv_score is not None:
                            st.progress(float(srv_score))
                            st.write(f"{srv_score:.2f}/1.00")
                        else:
                            st.write("N/A")
                    
                    with cols[2]:
                        st.write("**Details:**")
                        if 'details' in service_result and service_result['details']:
                            st.json(service_result['details'])
                        else:
                            st.write("No detailed data available")
    
    # If there's detailed data for a single service
    elif 'details' in result and result['details']:
        with st.expander("Detailed Information"):
            st.json(result['details'])

# Sidebar menu
st.sidebar.title("Email Verification System")
menu = st.sidebar.selectbox(
    "Navigation",
    ["Single Email Verification", "Bulk Verification", "Email Lists", "API Keys", "Help"]
)

# Main content
if menu == "Single Email Verification":
    st.title("Single Email Verification")
    st.write("Verify a single email address using one or multiple services.")
    
    # Check if any API keys are configured
    available_services = verification_manager.get_available_services()
    if not available_services:
        st.warning("No verification services have API keys configured. Please set up API keys in the 'API Keys' section.")
    
    # Email input
    email = st.text_input("Email Address", placeholder="example@domain.com")
    
    # Service selection
    col1, col2 = st.columns(2)
    with col1:
        service_options = ["All Available Services"] + available_services
        selected_service = st.selectbox("Select Verification Service", service_options)
    
    with col2:
        st.write("Available Services:")
        for service in available_services:
            st.write(f"- {service.capitalize()}")
    
    # Verify button
    if st.button("Verify Email"):
        if not email:
            st.error("Please enter an email address.")
        else:
            # Determine which service to use
            service_name = None if selected_service == "All Available Services" else selected_service
            
            # Verify email
            result = verify_single_email(email, service_name)
            
            # Display result
            display_verification_result(result)
    
    # History
    if email:
        st.subheader("Verification History")
        history = verification_manager.get_verification_history(email)
        
        if not history:
            st.info("No verification history found for this email.")
        else:
            history_df = pd.DataFrame(history)
            history_df['verification_date'] = pd.to_datetime(history_df['verification_date'])
            history_df = history_df.sort_values('verification_date', ascending=False)
            
            # Display as table
            st.dataframe(
                history_df[['provider', 'is_valid', 'score', 'verification_date']],
                use_container_width=True
            )

elif menu == "Bulk Verification":
    st.title("Bulk Email Verification")
    st.write("Verify multiple email addresses at once.")
    
    # Check if any API keys are configured
    available_services = verification_manager.get_available_services()
    if not available_services:
        st.warning("No verification services have API keys configured. Please set up API keys in the 'API Keys' section.")
        st.stop()
    
    # Input method: text or file
    input_method = st.radio("Input Method", ["Enter Emails", "Upload CSV File"])
    
    emails_to_verify = []
    
    if input_method == "Enter Emails":
        email_text = st.text_area(
            "Enter email addresses (one per line)",
            placeholder="example1@domain.com\nexample2@domain.com\nexample3@domain.com"
        )
        
        if email_text:
            # Split by newlines and filter empty lines
            emails_to_verify = [e.strip() for e in email_text.split('\n') if e.strip()]
            st.info(f"{len(emails_to_verify)} email(s) entered.")
    
    else:  # Upload CSV
        uploaded_file = st.file_uploader("Upload CSV file with email addresses", type=["csv"])
        
        if uploaded_file:
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            try:
                # Read CSV
                df = pd.read_csv(tmp_path)
                
                # Look for email column
                email_columns = [col for col in df.columns if 'email' in col.lower()]
                
                if email_columns:
                    # Use the first column that contains 'email'
                    email_col = email_columns[0]
                    emails_to_verify = df[email_col].dropna().tolist()
                    st.info(f"{len(emails_to_verify)} email(s) found in column '{email_col}'.")
                else:
                    st.error("No column containing 'email' found in the CSV file.")
            except Exception as e:
                st.error(f"Error reading CSV file: {str(e)}")
            
            # Clean up
            try:
                os.unlink(tmp_path)
            except:
                pass
    
    # Service selection
    service_options = ["All Available Services"] + available_services
    selected_service = st.selectbox("Select Verification Service", service_options)
    service_name = None if selected_service == "All Available Services" else selected_service
    
    # Verify button
    if st.button("Verify Emails"):
        if not emails_to_verify:
            st.error("No emails to verify. Please enter emails or upload a CSV file.")
        else:
            # Limit the number of emails to verify at once
            max_emails = 100
            if len(emails_to_verify) > max_emails:
                st.warning(f"Too many emails. Limiting to first {max_emails} emails.")
                emails_to_verify = emails_to_verify[:max_emails]
            
            # Verify emails
            results = verify_bulk_emails(emails_to_verify, service_name)
            
            if 'error' in results:
                st.error(f"Error: {results['error']}")
            elif 'results' in results:
                # Convert results to DataFrame
                if isinstance(results['results'], list):
                    # Create a list of dictionaries for the DataFrame
                    df_data = []
                    
                    for r in results['results']:
                        if isinstance(r, dict) and 'email' in r:
                            entry = {
                                'email': r.get('email'),
                                'is_valid': r.get('is_valid'),
                                'score': r.get('score'),
                                'provider': r.get('provider', '')
                            }
                            
                            # If we have aggregated results
                            if 'results' in r and isinstance(r['results'], dict):
                                for srv, srv_result in r['results'].items():
                                    if isinstance(srv_result, dict):
                                        entry[f"{srv}_valid"] = srv_result.get('is_valid')
                                        entry[f"{srv}_score"] = srv_result.get('score')
                            
                            df_data.append(entry)
                    
                    if df_data:
                        result_df = pd.DataFrame(df_data)
                        
                        # Display results
                        st.subheader("Verification Results")
                        st.dataframe(result_df, use_container_width=True)
                        
                        # Download option
                        csv = result_df.to_csv(index=False)
                        st.download_button(
                            "Download Results as CSV",
                            csv,
                            "email_verification_results.csv",
                            "text/csv",
                            key='download-csv'
                        )
                    else:
                        st.error("No valid results returned.")
                else:
                    st.error("Unexpected result format.")
            else:
                st.error("No results returned.")

elif menu == "Email Lists":
    st.title("Email Lists")
    st.write("Manage your email lists for verification and outreach.")
    
    # Tabs for different list operations
    tabs = st.tabs(["View Lists", "Create List", "Add to List", "Import/Export"])
    
    with tabs[0]:  # View Lists
        st.subheader("Your Email Lists")
        
        # Refresh button
        if st.button("Refresh Lists"):
            st.experimental_rerun()
        
        # Get all lists
        lists = list_manager.get_lists()
        
        if not lists:
            st.info("No email lists found. Create a new list to get started.")
        else:
            # Display lists as expandable sections
            for email_list in lists:
                with st.expander(f"{email_list['name']} ({email_list['email_count']} emails)"):
                    st.write(f"**Description:** {email_list['description'] or 'No description'}")
                    st.write(f"**Created:** {email_list['created_at']}")
                    st.write(f"**Updated:** {email_list['updated_at']}")
                    
                    # Button to view entries
                    if st.button("View Entries", key=f"view_{email_list['list_id']}"):
                        entries = list_manager.get_list_entries(email_list['list_id'])
                        
                        if not entries:
                            st.info("No entries in this list.")
                        else:
                            st.dataframe(pd.DataFrame(entries), use_container_width=True)
    
    with tabs[1]:  # Create List
        st.subheader("Create New List")
        
        list_name = st.text_input("List Name", placeholder="My Contact List")
        list_description = st.text_area("Description", placeholder="Optional description for this list")
        
        if st.button("Create List"):
            if not list_name:
                st.error("Please enter a list name.")
            else:
                result = list_manager.create_list(list_name, list_description)
                
                if 'error' in result:
                    st.error(f"Error: {result['error']}")
                else:
                    st.success(f"List '{list_name}' created successfully!")
    
    with tabs[2]:  # Add to List
        st.subheader("Add Email to List")
        
        # Get lists for dropdown
        lists = list_manager.get_lists()
        list_options = {l['name']: l['list_id'] for l in lists}
        
        if not list_options:
            st.info("No lists available. Please create a list first.")
        else:
            selected_list = st.selectbox("Select List", list(list_options.keys()))
            list_id = list_options[selected_list]
            
            # Email input
            email = st.text_input("Email Address", key="add_email", placeholder="example@domain.com")
            
            # Additional info
            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input("First Name", placeholder="Optional")
                company = st.text_input("Company", placeholder="Optional")
            
            with col2:
                last_name = st.text_input("Last Name", placeholder="Optional")
                position = st.text_input("Position", placeholder="Optional")
            
            if st.button("Add to List"):
                if not email:
                    st.error("Please enter an email address.")
                else:
                    result = list_manager.add_email_to_list(
                        list_id=list_id,
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        company=company,
                        position=position
                    )
                    
                    if 'error' in result:
                        st.error(f"Error: {result['error']}")
                    elif result.get('updated', False):
                        st.success(f"Email {email} updated in list!")
                    elif result.get('added', False):
                        st.success(f"Email {email} added to list!")
    
    with tabs[3]:  # Import/Export
        st.subheader("Import/Export Lists")
        
        # Get lists for dropdown
        lists = list_manager.get_lists()
        list_options = {l['name']: l['list_id'] for l in lists}
        
        if not list_options:
            st.info("No lists available. Please create a list first.")
        else:
            selected_list = st.selectbox("Select List", list(list_options.keys()), key="imp_exp_list")
            list_id = list_options[selected_list]
            
            # Tabs for import and export
            imp_exp_tabs = st.tabs(["Import from CSV", "Export to CSV"])
            
            with imp_exp_tabs[0]:  # Import
                st.write("Import emails from a CSV file into the selected list.")
                st.write("The CSV should have columns for: email, first_name, last_name, company, position")
                
                uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
                
                if uploaded_file:
                    # Save to temp file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_path = tmp_file.name
                    
                    # Preview the file
                    try:
                        df = pd.read_csv(tmp_path)
                        st.write("Preview:")
                        st.dataframe(df.head(), use_container_width=True)
                        
                        if st.button("Import Data"):
                            result = list_manager.import_from_csv(list_id, tmp_path)
                            
                            if 'error' in result:
                                st.error(f"Error: {result['error']}")
                            else:
                                st.success(f"Import successful! Added: {result.get('added', 0)}, Updated: {result.get('updated', 0)}, Errors: {result.get('errors', 0)}")
                    
                    except Exception as e:
                        st.error(f"Error reading CSV file: {str(e)}")
                    
                    # Clean up
                    try:
                        os.unlink(tmp_path)
                    except:
                        pass
            
            with imp_exp_tabs[1]:  # Export
                st.write("Export the selected list to a CSV file.")
                
                if st.button("Generate Export"):
                    entries = list_manager.get_list_entries(list_id)
                    
                    if not entries:
                        st.info("No entries to export in this list.")
                    else:
                        df = pd.DataFrame(entries)
                        csv = df.to_csv(index=False)
                        
                        st.download_button(
                            "Download CSV",
                            csv,
                            f"{selected_list.replace(' ', '_')}_export.csv",
                            "text/csv",
                            key="download-list-csv"
                        )

elif menu == "API Keys":
    st.title("API Keys Configuration")
    st.write("Configure API keys for the verification services.")
    
    # Status of API keys
    st.subheader("API Key Status")
    
    for service_name in verification_manager.services.keys():
        service_name_lower = service_name.lower()
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if st.session_state.api_keys_configured.get(service_name_lower, False):
                st.success(f"{service_name.capitalize()} ✓")
            else:
                st.error(f"{service_name.capitalize()} ✗")
        
        with col2:
            # Input field for API key
            api_key = st.text_input(
                f"{service_name.capitalize()} API Key",
                type="password",
                key=f"input_{service_name_lower}"
            )
            
            # Save button
            if st.button(f"Save {service_name.capitalize()} API Key", key=f"save_{service_name_lower}"):
                if api_key:
                    save_api_key(service_name_lower, api_key)
                else:
                    st.error("Please enter an API key.")
    
    # API Documentation links
    st.subheader("API Documentation")
    st.markdown("""
    - [ZeroBounce API](https://www.zerobounce.net/docs/)
    - [MailboxLayer API](https://mailboxlayer.com/documentation)
    - [NeutrinoAPI](https://www.neutrinoapi.com/api/email-validate/)
    - [Spokeo API](https://www.spokeo.com/)
    - [Hunter.io API](https://hunter.io/api-documentation)
    """)

else:  # Help
    st.title("Help & Documentation")
    
    st.header("Email Verification System")
    st.write("""
    This application provides comprehensive email verification functionality using multiple
    verification services to validate email addresses and manage email lists efficiently.
    Perfect for maintaining clean contact lists and validating email addresses before sending campaigns.
    """)
    
    st.header("Features")
    st.markdown("""
    - **Single Email Verification**
        - Verify individual email addresses
        - Choose specific verification service or use all available services
        - View detailed validation results and scores
        - Access verification history
        
    - **Bulk Verification**
        - Upload CSV files for bulk verification
        - Process up to 100 emails simultaneously
        - Download verification results as CSV
        - View aggregate validation statistics
        
    - **Email List Management**
        - Create and manage multiple email lists
        - Import/Export lists via CSV
        - Add custom fields (name, company, position)
        - Track list creation and update dates
        
    - **Service Integration**
        - Multiple verification services for accuracy
        - Aggregated validation scores
        - Detailed validation results per service
    """)
    
    st.header("Verification Services")
    st.markdown("""
    Integrated verification services with their specialties:
    
    1. **ZeroBounce**
        - Comprehensive email validation
        - Catch-all domain detection
        - MX record validation
        - SMTP verification
        
    2. **MailboxLayer**
        - Syntax validation
        - Typo detection
        - Disposable email detection
        - Role-based email check
        
    3. **NeutrinoAPI**
        - SMTP deep validation
        - Domain quality scoring
        - Abuse detection
        - Location verification
        
    4. **Spokeo**
        - People search capabilities
        - Social media verification
        - Historical email data
        - Owner information
        
    5. **Hunter.io**
        - Domain email verification
        - Company email formats
        - Professional email scoring
        - B2B email validation
    
    Configure API keys in the "API Keys" section to enable these services.
    """)
    
    st.header("Usage Guide")
    st.markdown("""
    1. **Initial Setup**
        - Navigate to "API Keys" section
        - Configure at least one verification service
        - Test the connection with a sample email
        
    2. **Single Email Verification**
        - Enter email address
        - Select verification service(s)
        - View detailed results and history
        
    3. **Bulk Verification**
        - Prepare CSV with required columns
        - Upload file (max 100 emails per batch)
        - Download verification results
        
    4. **List Management**
        - Create lists with meaningful names
        - Import existing contacts
        - Add/Update entries manually
        - Export lists for backup
    """)
    
    st.header("CSV Format")
    st.markdown("""
    For bulk operations and list imports, prepare CSV files with these columns:
    - email (required)
    - first_name
    - last_name
    - company
    - position
    
    Example:
    ```
    email,first_name,last_name,company,position
    john@example.com,John,Doe,ACME Inc,Manager
    ```
    """)

# Initialize database on startup
@st.cache_data
def serve_static_files():
    # Create static directory if it doesn't exist
    if not os.path.exists("static"):
        os.makedirs("static")
    return True

if __name__ == "__main__":
    # Initialize static file serving
    serve_static_files()
    
    # Check for environment folder
    if not os.path.exists(".streamlit"):
        os.makedirs(".streamlit")
    
    # Create Streamlit config
    if not os.path.exists(".streamlit/config.toml"):
        with open(".streamlit/config.toml", "w") as f:
            f.write("""
[server]
headless = true
address = "0.0.0.0"
port = 5000
            """)