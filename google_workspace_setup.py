#!/usr/bin/env python3
"""
Google Workspace Setup for 1Password SSO

This script helps automate the setup of Google Workspace for 1Password SSO integration
by handling the creation of the SAML application using the Google Admin SDK.
"""

import argparse
import os
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
import pickle
import random
import string
import time

# Define scopes needed for Google Admin SDK
SCOPES = [
    'https://www.googleapis.com/auth/admin.directory.user',
    'https://www.googleapis.com/auth/admin.directory.group',
    'https://www.googleapis.com/auth/admin.directory.rolemanagement',
    'https://www.googleapis.com/auth/admin.directory.customer',
    'https://www.googleapis.com/auth/admin.directory.resource.calendar'
]

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Configure Google Workspace for 1Password SSO')
    
    parser.add_argument('--admin-email', required=True, 
                      help='Admin email for Google Workspace')
    parser.add_argument('--domain', required=True, 
                      help='Your domain name (e.g., example.com)')
    parser.add_argument('--service-account-file', 
                      help='Path to service account key file')
    parser.add_argument('--scim-bridge-url', required=True, 
                      help='URL of the deployed SCIM Bridge')
    parser.add_argument('--credentials-file', default='credentials.json',
                      help='Path to OAuth client ID credentials file')
    parser.add_argument('--token-file', default='token.pickle',
                      help='Path to save the generated token')
    
    return parser.parse_args()

def get_credentials(args):
    """Get valid user credentials from storage or user authorization."""
    creds = None
    
    # Check if we have a token.pickle file with credentials
    if os.path.exists(args.token_file):
        with open(args.token_file, 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if args.service_account_file:
                # Use service account
                creds = service_account.Credentials.from_service_account_file(
                    args.service_account_file, scopes=SCOPES)
                creds = creds.with_subject(args.admin_email)
            else:
                # Use OAuth flow
                if os.path.exists(args.credentials_file):
                    flow = InstalledAppFlow.from_client_secrets_file(args.credentials_file, SCOPES)
                    creds = flow.run_local_server(port=0)
                else:
                    raise FileNotFoundError(f"Credentials file {args.credentials_file} not found")
            
            # Save the credentials for the next run
            with open(args.token_file, 'wb') as token:
                pickle.dump(creds, token)
    
    return creds

def setup_saml_application(service, args):
    """Set up a SAML application for 1Password in Google Workspace."""
    print("NOTE: Google Admin SDK API does not provide full support for creating SAML apps programmatically.")
    print("This script will guide you through the manual steps needed in the Google Admin console.")
    
    # Generate a unique application name
    app_name = f"1Password SSO ({time.strftime('%Y-%m-%d')})"
    
    print("\n===== Manual Configuration Steps =====")
    print("1. Log in to the Google Workspace Admin console: https://admin.google.com")
    print("2. Navigate to: Apps > Web and mobile apps")
    print("3. Click 'Add app' > 'Add custom SAML app'")
    print(f"4. Name the application: '{app_name}'")
    print("\n5. Configure Service Provider Details:")
    print(f"   - ACS URL: {args.scim_bridge_url}/sso/acs")
    print("   - Entity ID: https://1password.com/sso")
    print("   - Start URL: https://my.1password.com/signin")
    print("\n6. Configure Attribute Mapping:")
    print("   - Add the following attribute mappings:")
    print("     * Primary email -> email")
    print("     * First name -> firstName")
    print("     * Last name -> lastName")
    print("\n7. Set Access Settings:")
    print("   - ON for everyone (or select specific organizational units)")
    
    # Try to retrieve user information to confirm API access is working
    try:
        # List first 10 users to confirm API access
        results = service.users().list(domain=args.domain, maxResults=10).execute()
        users = results.get('users', [])
        
        if users:
            print("\nAPI Access Confirmed - Sample users from your domain:")
            for user in users:
                print(f"  - {user.get('primaryEmail')}")
        
        # List groups to help with assigning access
        results = service.groups().list(domain=args.domain, maxResults=10).execute()
        groups = results.get('groups', [])
        
        if groups:
            print("\nGroups you might want to grant access to:")
            for group in groups:
                print(f"  - {group.get('name')} ({group.get('email')})")
        
    except HttpError as error:
        print(f"API Error: {error}")
        
    print("\n===== SCIM Bridge Configuration =====")
    print("After setting up the SAML application in Google Workspace, configure the 1Password SCIM Bridge:")
    
    # Generate a bearer token for demonstration
    bearer_token = ''.join(random.choices(string.ascii_letters + string.digits, k=40))
    
    print("\n1. In the 1Password Admin console (https://start.1password.com):")
    print("   a. Navigate to Settings > Provisioning > Directory Sync")
    print("   b. Click 'Set up' and choose 'Google Workspace'")
    print(f"   c. Enter the SCIM Bridge URL: {args.scim_bridge_url}")
    print("   d. Create a bearer token when prompted")
    print("\n2. In Google Workspace Admin console:")
    print("   a. Go to the SAML application you created")
    print("   b. Under 'Service provider details', add the following:")
    print(f"      - SCIM URL: {args.scim_bridge_url}/scim")
    print("      - Add the bearer token you created in 1Password")
    
    return True

def main():
    """Main function to orchestrate the Google Workspace setup for 1Password SSO."""
    args = parse_arguments()
    
    try:
        # Get credentials
        creds = get_credentials(args)
        
        # Build the Admin SDK Directory service
        service = build('admin', 'directory_v1', credentials=creds)
        
        # Set up SAML application
        setup_saml_application(service, args)
        
        print("\n===== Configuration Complete =====")
        print("Follow the manual steps above to complete the configuration.")
        print("\nFor troubleshooting and further information, refer to:")
        print("- 1Password documentation: https://support.1password.com/sso-configure/")
        print("- Google Workspace SAML Apps: https://support.google.com/a/answer/6087519")
        
    except Exception as e:
        print(f"Error during setup: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())