#!/usr/bin/env python3
"""
1Password Configuration Tool

This script helps with the final configuration steps for 1Password SSO integration.
It guides users through configuring the 1Password Admin Console and testing the integration.
"""

import argparse
import json
import os
import requests
import sys
from datetime import datetime
import uuid

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Configure 1Password SSO with Google Workspace')
    
    parser.add_argument('--scim-bridge-url', required=True, 
                      help='URL of the deployed SCIM Bridge')
    parser.add_argument('--bearer-token',
                      help='Bearer token for SCIM Bridge authentication (if already created)')
    parser.add_argument('--config-file', default='1password-config.json',
                      help='Path to save the configuration')
    parser.add_argument('--verify', action='store_true',
                      help='Verify the SCIM Bridge configuration')
    
    return parser.parse_args()

def generate_bearer_token():
    """Generate a random bearer token."""
    return str(uuid.uuid4())

def save_configuration(args, bearer_token=None):
    """Save the configuration to a file."""
    config = {
        "scim_bridge_url": args.scim_bridge_url,
        "bearer_token": bearer_token or args.bearer_token,
        "configured_at": datetime.now().isoformat()
    }
    
    with open(args.config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"Configuration saved to {args.config_file}")
    
    # Create a redacted version for display
    display_config = config.copy()
    if display_config["bearer_token"]:
        display_config["bearer_token"] = display_config["bearer_token"][:5] + "..." + display_config["bearer_token"][-5:]
    
    print("\nConfiguration Summary:")
    print(json.dumps(display_config, indent=2))
    
    return config

def verify_scim_bridge(url, token):
    """Verify that the SCIM Bridge is accessible."""
    if not token:
        print("No bearer token provided, skipping verification")
        return False
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/scim+json"
    }
    
    try:
        # Test the SCIM endpoint
        response = requests.get(f"{url}/scim/Users", headers=headers)
        
        if response.status_code == 200:
            print("✅ SCIM Bridge verification successful!")
            print("  Users endpoint is accessible")
            return True
        else:
            print(f"❌ SCIM Bridge verification failed with status code: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error connecting to SCIM Bridge: {e}")
        return False

def main():
    """Main function to orchestrate the 1Password configuration."""
    args = parse_arguments()
    
    # Generate bearer token if not provided
    bearer_token = args.bearer_token
    if not bearer_token:
        bearer_token = generate_bearer_token()
        print(f"Generated new bearer token: {bearer_token}")
        print("Keep this token secure - you'll need it to configure the SCIM Bridge!")
    
    # Save configuration
    config = save_configuration(args, bearer_token)
    
    # If verify flag is set, test the SCIM Bridge
    if args.verify:
        if verify_scim_bridge(args.scim_bridge_url, config["bearer_token"]):
            print("\n🎉 Your 1Password SCIM Bridge is correctly configured and accessible!")
        else:
            print("\n⚠️ Unable to verify SCIM Bridge configuration")
            print("Please check your configuration and try again")
    
    print("\n===== 1Password Admin Console Configuration =====")
    print("Complete these steps in the 1Password Admin console (https://start.1password.com):")
    print("\n1. Go to Settings > Authentication > Single Sign-On")
    print("2. Click 'Set up SSO'")
    print("3. Choose 'Google Workspace' as your identity provider")
    print("4. Configure the following settings:")
    print(f"   - Sign-in URL: Your Google Workspace SSO URL")
    print("   - IdP Entity ID: https://accounts.google.com/o/saml2?idpid=YOUR_IDP_ID")
    print("     (Get this from Google Workspace Admin Console > Security > Set up single sign-on)")
    print("\n5. Go to Settings > Provisioning > Directory Sync")
    print("6. Click 'Set up directory sync'")
    print("7. Choose 'Google Workspace' as your identity source")
    print("8. Configure the SCIM Bridge with the following details:")
    print(f"   - SCIM Bridge URL: {args.scim_bridge_url}")
    print(f"   - Bearer Token: {bearer_token}")
    
    print("\n===== Testing the Integration =====")
    print("After completing the configuration:")
    print("1. Assign a test user to the 1Password SAML application in Google Workspace")
    print("2. Login to https://my.1password.com/signin with that user")
    print("3. Verify that SSO authentication works correctly")
    
    return 0

if __name__ == "__main__":
    exit(main())