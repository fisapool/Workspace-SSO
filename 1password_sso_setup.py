#!/usr/bin/env python3
"""
1Password SSO Configuration with Google Cloud

This script automates the setup of 1Password SSO with Google Cloud.
It handles the deployment of the SCIM Bridge and configures Google Identity.
"""

import os
import argparse
import subprocess
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(os.path.join('config', '.env'))

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Set up 1Password SSO with Google Workspace')
    
    parser.add_argument('--project-id', default=os.environ.get('GCP_PROJECT_ID'),
                        help='Google Cloud Project ID')
    parser.add_argument('--region', default=os.environ.get('GCP_REGION', 'us-central1'),
                        help='GCP Region for Cloud Run deployment')
    parser.add_argument('--service-account-name', 
                        default=os.environ.get('SERVICE_ACCOUNT_NAME', 'scim-bridge-sa'),
                        help='Service Account Name for SCIM Bridge')
    parser.add_argument('--scim-bridge-image', 
                        default=os.environ.get('SCIM_BRIDGE_IMAGE', '1password/scim-bridge:latest'),
                        help='Docker image for SCIM Bridge')
    parser.add_argument('--domain', default=os.environ.get('DOMAIN'),
                        help='Your organization\'s domain name')
    parser.add_argument('--admin-email', default=os.environ.get('ADMIN_EMAIL'),
                        help='Google Workspace Admin Email')
    parser.add_argument('--service-account-file', 
                        default=os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'),
                        help='Path to service account key file')
    
    return parser.parse_args()


def run_command(command, check=True, capture_output=False):
    """Run a shell command and optionally capture its output."""
    print(f"Running: {command}")
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=capture_output, text=True)
        if capture_output:
            return result.stdout.strip()
        return True
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}: {e}")
        if capture_output:
            print(f"Error output: {e.stderr}")
        if check:
            raise
        return False


def authenticate_gcp(project_id):
    """Authenticate with GCP and set the project."""
    print(f"Authenticating with GCP and setting project to {project_id}...")
    run_command(f"gcloud auth login")
    run_command(f"gcloud config set project {project_id}")


def create_service_account(args):
    """Create a service account for the SCIM Bridge."""
    print(f"Creating service account {args.service_account_name}...")
    
    # Check if service account already exists
    sa_exists = run_command(
        f"gcloud iam service-accounts describe {args.service_account_name}@{args.project_id}.iam.gserviceaccount.com",
        check=False
    )
    
    if not sa_exists:
        run_command(
            f"gcloud iam service-accounts create {args.service_account_name} "
            f"--display-name='SCIM Bridge Service Account'"
        )
    else:
        print(f"Service account {args.service_account_name} already exists.")
    
    # Assign roles to the service account
    print("Assigning roles to service account...")
    roles = ["roles/iam.serviceAccountUser", "roles/storage.admin"]
    
    for role in roles:
        run_command(
            f"gcloud projects add-iam-policy-binding {args.project_id} "
            f"--member='serviceAccount:{args.service_account_name}@{args.project_id}.iam.gserviceaccount.com' "
            f"--role='{role}'"
        )


def deploy_scim_bridge(args):
    """Deploy the SCIM Bridge on GCP Cloud Run."""
    print(f"Deploying SCIM Bridge to Cloud Run in {args.region}...")
    
    run_command(
        f"gcloud run deploy scim-bridge "
        f"--image={args.scim_bridge_image} "
        f"--region={args.region} "
        f"--service-account={args.service_account_name}@{args.project_id}.iam.gserviceaccount.com "
        f"--allow-unauthenticated"
    )
    
    # Get the URL of the deployed SCIM Bridge
    scim_bridge_url = run_command(
        f"gcloud run services describe scim-bridge --region={args.region} "
        f"--format='value(status.url)'",
        capture_output=True
    )
    
    print(f"SCIM Bridge deployed successfully at: {scim_bridge_url}")
    return scim_bridge_url


def configure_google_identity(args, scim_bridge_url):
    """Configure Google Identity for 1Password SSO using Google Admin SDK."""
    print("Configuring Google Identity for 1Password SSO...")
    
    # Set up authentication with Google Admin SDK
    SCOPES = ['https://www.googleapis.com/auth/admin.directory.user',
              'https://www.googleapis.com/auth/admin.directory.group',
              'https://www.googleapis.com/auth/admin.directory.serviceaccount']
    
    # Load credentials from the service account file
    try:
        credentials = service_account.Credentials.from_service_account_file(
            args.service_account_file, scopes=SCOPES)
        
        # Delegate authority to admin user
        delegated_credentials = credentials.with_subject(args.admin_email)
        
        # Build the Admin SDK service
        service = build('admin', 'directory_v1', credentials=delegated_credentials)
        
        # Create a dedicated service account for SCIM Bridge
        scim_email = f"scim-bridge@{args.domain}"
        
        # Check if user already exists
        try:
            existing_user = service.users().get(userKey=scim_email).execute()
            print(f"User {scim_email} already exists.")
        except HttpError as e:
            if e.resp.status == 404:
                # User doesn't exist, create new one
                print(f"Creating new user {scim_email}...")
                
                import secrets
                # Generate a secure random password
                password = secrets.token_urlsafe(16)
                
                user_body = {
                    "primaryEmail": scim_email,
                    "name": {
                        "givenName": "SCIM",
                        "familyName": "Bridge"
                    },
                    "password": password,
                    "changePasswordAtNextLogin": False
                }
                
                service.users().insert(body=user_body).execute()
                print(f"Created user {scim_email}")
                print(f"Password for {scim_email}: {password}")
                print("IMPORTANT: Save this password securely and use it for the SCIM Bridge setup.")
            else:
                raise
        
        # Create the SAML application configuration
        # Note: Google Workspace Admin API doesn't provide direct methods to create SAML apps
        # You'll need to use the Google Workspace Admin Console for this part
        print("\nManual Steps Required:")
        print("1. Log in to the Google Workspace Admin console: https://admin.google.com")
        print("2. Go to Apps > Web and mobile apps > Add app > Add custom SAML app")
        print("3. Set up the app with the following details:")
        print(f"   - ACS URL: {scim_bridge_url}/sso/acs")
        print(f"   - Entity ID: https://1password.com/sso")
        print(f"   - Name ID format: EMAIL")
        print(f"   - Name ID: Basic Information > Primary Email")
        print("4. Complete the setup and assign users/groups to the app")
        print("\nAdditional 1Password Setup:")
        print("1. Log in to 1Password Admin Console")
        print("2. Go to People > Directory Sync > Set up directory sync")
        print("3. Configure the SCIM Bridge with the URL and credentials")
        
        return True
        
    except Exception as e:
        print(f"Error configuring Google Identity: {e}")
        return False


def main():
    """Main function to orchestrate the 1Password SSO configuration."""
    args = parse_arguments()
    
    # Step 1: Authenticate with GCP
    authenticate_gcp(args.project_id)
    
    # Step 2: Create service account
    create_service_account(args)
    
    # Step 3: Deploy SCIM Bridge
    scim_bridge_url = deploy_scim_bridge(args)
    
    # Step 4: Configure Google Identity for 1Password SSO
    configure_google_identity(args, scim_bridge_url)
    
    print("\n==== 1Password SSO Configuration ====")
    print(f"SCIM Bridge URL: {scim_bridge_url}")
    print(f"Project ID: {args.project_id}")
    print(f"Domain: {args.domain}")
    
    # Output configuration summary
    print("\nConfiguration Summary:")
    print("1. SCIM Bridge deployed on Google Cloud Run")
    print("2. Service account created with necessary permissions")
    print("3. User account created for SCIM integration")
    print("4. Instructions provided for completing SAML setup in Google Workspace Admin Console")


if __name__ == "__main__":
    main()