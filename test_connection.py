#!/usr/bin/env python3
"""
Test Connection Script for 1Password SCIM Bridge

This script tests the connection to the 1Password SCIM Bridge and Google Workspace.
"""

import argparse
import json
import requests
import sys
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Test 1Password SCIM Bridge and Google Workspace connection')
    
    parser.add_argument('--scim-bridge-url', required=True, 
                      help='URL of the deployed SCIM Bridge')
    parser.add_argument('--bearer-token', required=True,
                      help='Bearer token for SCIM Bridge authentication')
    parser.add_argument('--service-account-file', 
                      help='Path to service account key file')
    parser.add_argument('--admin-email',
                      help='Admin email for Google Workspace')
    parser.add_argument('--domain',
                      help='Your domain name (e.g., example.com)')
    
    return parser.parse_args()

def test_scim_bridge(url, token):
    """Test connection to the SCIM Bridge."""
    print("\n===== Testing SCIM Bridge Connection =====")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/scim+json"
    }
    
    endpoints = [
        "/scim/ServiceProviderConfig",
        "/scim/Users",
        "/scim/Groups"
    ]
    
    all_successful = True
    
    for endpoint in endpoints:
        full_url = f"{url}{endpoint}"
        print(f"Testing endpoint: {full_url}")
        
        try:
            response = requests.get(full_url, headers=headers)
            
            if response.status_code == 200:
                print(f"  ✅ Success! Status code: {response.status_code}")
                
                # Show a sample of the response
                try:
                    data = response.json()
                    if "Resources" in data and data["Resources"]:
                        print(f"  Found {len(data['Resources'])} resources")
                    elif "schemas" in data:
                        print(f"  Schema: {data['schemas']}")
                except json.JSONDecodeError:
                    print("  (Response is not valid JSON)")
            else:
                print(f"  ❌ Failed! Status code: {response.status_code}")
                print(f"  Response: {response.text}")
                all_successful = False
                
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Error: {e}")
            all_successful = False
    
    return all_successful

def test_google_workspace(service_account_file, admin_email, domain):
    """Test connection to Google Workspace."""
    if not service_account_file or not admin_email or not domain:
        print("\n===== Skipping Google Workspace Test =====")
        print("Service account file, admin email, or domain not provided")
        return None
    
    print("\n===== Testing Google Workspace Connection =====")
    
    # Define scopes needed for Google Admin SDK
    SCOPES = [
        'https://www.googleapis.com/auth/admin.directory.user',
        'https://www.googleapis.com/auth/admin.directory.group'
    ]
    
    try:
        # Authenticate with service account
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file, scopes=SCOPES)
        
        # Delegate authority to admin user
        delegated_credentials = credentials.with_subject(admin_email)
        
        # Build the Admin SDK Directory service
        service = build('admin', 'directory_v1', credentials=delegated_credentials)
        
        # Test listing users
        print(f"Testing: List users in domain {domain}")
        response = service.users().list(domain=domain, maxResults=5).execute()
        users = response.get('users', [])
        
        if users:
            print(f"  ✅ Success! Found {len(users)} users")
            print("  Sample user emails:")
            for user in users:
                print(f"    - {user.get('primaryEmail')}")
        else:
            print("  ✅ Connection successful, but no users found")
        
        # Test listing groups
        print(f"Testing: List groups in domain {domain}")
        response = service.groups().list(domain=domain, maxResults=5).execute()
        groups = response.get('groups', [])
        
        if groups:
            print(f"  ✅ Success! Found {len(groups)} groups")
            print("  Sample group names:")
            for group in groups:
                print(f"    - {group.get('name')} ({group.get('email')})")
        else:
            print("  ✅ Connection successful, but no groups found")
        
        return service
        
    except HttpError as error:
        print(f"  ❌ API Error: {error}")
        return None
    
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None

def main():
    """Main function to orchestrate the connection tests."""
    args = parse_arguments()
    
    # Test SCIM Bridge connection
    scim_success = test_scim_bridge(args.scim_bridge_url, args.bearer_token)
    
    # Test Google Workspace connection
    gws_service = test_google_workspace(args.service_account_file, args.admin_email, args.domain)
    
    # Print summary
    print("\n===== Connection Test Summary =====")
    
    if scim_success:
        print("✅ SCIM Bridge: Connection successful")
    else:
        print("❌ SCIM Bridge: Connection failed")
    
    if gws_service:
        print("✅ Google Workspace: Connection successful")
    elif args.service_account_file and args.admin_email and args.domain:
        print("❌ Google Workspace: Connection failed")
    else:
        print("⚠️ Google Workspace: Test skipped (missing parameters)")
    
    print("\nFor troubleshooting:")
    print("1. Verify the SCIM Bridge is running and accessible")
    print("2. Check that the bearer token is correct")
    print("3. Ensure the service account has the necessary permissions")
    print("4. Verify the admin email has admin privileges in Google Workspace")
    
    return 0 if scim_success and (gws_service or not args.service_account_file) else 1

if __name__ == "__main__":
    exit(main())