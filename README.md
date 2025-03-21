# Google Workspace SSO Integration Tools

A Streamlit application for email verification and list management using multiple verification services.

## Current Features

- Single Email Verification
- Bulk Email Verification
- Email List Management
- Multiple Service Integration:
  - ZeroBounce
  - MailboxLayer
  - NeutrinoAPI
  - Spokeo
  - Hunter.io
- Database Storage for Verification History
- Streamlit Dashboard Interface

## Coming Soon

- 1Password SSO configuration with Google Cloud
- Google Workspace SAML application setup
- Gmail API integration
- Custom SAML Applications Setup
- Automated Service Account Management

## Prerequisites

- Python 3.11+
- Required Python packages (see `requirements.txt`)

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/fisamy/Google-Workspace-SSO-Integration-Tools.git
   cd Google-Workspace-SSO-Integration-Tools

python3 -m venv env
source env/bin/activate  # On Windows use `env\Scripts\activate`

pip install -r requirements.txt

## Usage

Start the Streamlit application:
```bash
streamlit run app.py
```

## Configuration

1. Configure API keys for verification services:
   - ZeroBounce
   - MailboxLayer
   - NeutrinoAPI
   - Spokeo
   - Hunter.io

2. Access the dashboard at http://localhost:5000

## Scripts

- `app.py`: Main Streamlit application
- `email_verification_manager.py`: Email verification logic
- `email_list_manager.py`: List management functionality
- `database.py`: Database operations

## License

MIT License

## Parameters

Both scripts accept the following parameters:

| Parameter | Description | Required | Default |
|-----------|-------------|----------|---------|
| `--project-id` | Google Cloud Project ID | Yes | - |
| `--region` | GCP Region for Cloud Run deployment | No | us-central1 |
| `--service-account-name` | Service Account Name for SCIM Bridge | No | scim-bridge-sa |
| `--scim-bridge-image` | Docker image for SCIM Bridge | No | 1password/scim-bridge:latest |
| `--domain` | Your organization's domain name | Yes | - |
| `--admin-email` | Google Workspace Admin Email | Yes | - |
| `--service-account-file` | Path to service account key file (Python script only) | Yes (Python only) | - |

## Configuration

1. Set up Google Cloud credentials
2. Configure necessary environment variables
3. Configure API keys for verification services as needed:
   - ZeroBounce
   - MailboxLayer
   - NeutrinoAPI
   - Spokeo
   - Hunter.io

## Workflow

The scripts perform the following steps:

1. Authenticate with Google Cloud Platform
2. Create a service account for the SCIM Bridge
3. Assign necessary IAM roles to the service account
4. Deploy the 1Password SCIM Bridge on Google Cloud Run
5. Prepare configuration for Google Identity integration
6. Provide instructions for manual SAML application setup in Google Workspace

## Manual Steps Required

After running the script, you'll need to:

1. Generate a service account key if using the shell script
2. Set up a custom SAML application in Google Workspace Admin Console
3. Configure 1Password Admin Console for SCIM integration
4. Assign users/groups to the SAML application

## Scripts

- `app.py`: Main Streamlit application
- `1password_sso_setup.py`: 1Password SSO configuration
- `google_workspace_setup.py`: Google Workspace configuration
- `gmail_api.py`: Gmail API integration
- `email_verification_manager.py`: Email verification logic
- `email_list_manager.py`: List management functionality
- `database.py`: Database operations

## Troubleshooting

If you encounter issues during setup:

1. Check the Google Cloud Run logs for the SCIM Bridge deployment
2. Verify IAM permissions for the service account
3. Ensure the SAML configuration in Google Workspace is correct
4. Test the SCIM Bridge endpoint with a curl request to check if it's responding

For more detailed troubleshooting, refer to the 1Password SCIM Bridge documentation.

## License

MIT License
