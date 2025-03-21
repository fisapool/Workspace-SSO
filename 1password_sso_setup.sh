#!/bin/bash
# 1Password SSO Configuration with Google Cloud
# This script automates the deployment of the SCIM Bridge and setup of SSO

# Help function
function show_help {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --project-id PROJECT_ID         GCP Project ID (required)"
    echo "  --region REGION                 GCP Region (default: us-central1)"
    echo "  --service-account-name NAME     Service Account Name (default: scim-bridge-sa)"
    echo "  --scim-bridge-image IMAGE       SCIM Bridge Docker Image (default: 1password/scim-bridge:latest)"
    echo "  --domain DOMAIN                 Your domain name (required)"
    echo "  --admin-email EMAIL             Admin email for Google Workspace (required)"
    echo "  --help                          Show this help message"
    echo ""
    echo "Example:"
    echo "  $0 --project-id my-project --domain example.com --admin-email admin@example.com"
    exit 1
}

# Default values
REGION="us-central1"
SERVICE_ACCOUNT_NAME="scim-bridge-sa"
SCIM_BRIDGE_IMAGE="1password/scim-bridge:latest"

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --project-id) PROJECT_ID="$2"; shift ;;
        --region) REGION="$2"; shift ;;
        --service-account-name) SERVICE_ACCOUNT_NAME="$2"; shift ;;
        --scim-bridge-image) SCIM_BRIDGE_IMAGE="$2"; shift ;;
        --domain) DOMAIN="$2"; shift ;;
        --admin-email) ADMIN_EMAIL="$2"; shift ;;
        --help) show_help ;;
        *) echo "Unknown parameter: $1"; show_help ;;
    esac
    shift
done

# Check required parameters
if [ -z "$PROJECT_ID" ] || [ -z "$DOMAIN" ] || [ -z "$ADMIN_EMAIL" ]; then
    echo "Error: Missing required parameters"
    show_help
fi

echo "===== 1Password SSO Configuration with Google Cloud ====="
echo "Project ID:          $PROJECT_ID"
echo "Region:              $REGION"
echo "Service Account:     $SERVICE_ACCOUNT_NAME"
echo "SCIM Bridge Image:   $SCIM_BRIDGE_IMAGE"
echo "Domain:              $DOMAIN"
echo "Admin Email:         $ADMIN_EMAIL"
echo "==========================================================="
echo ""

# Authenticate with GCP
echo "Step 1: Authenticating with GCP..."
gcloud auth login
gcloud config set project $PROJECT_ID

# Create a service account for the SCIM Bridge
echo "Step 2: Creating service account for SCIM Bridge..."
if gcloud iam service-accounts describe "$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" &>/dev/null; then
    echo "Service account $SERVICE_ACCOUNT_NAME already exists."
else
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME --display-name "SCIM Bridge Service Account"
    echo "Service account $SERVICE_ACCOUNT_NAME created."
fi

# Assign roles to the service account
echo "Step 3: Assigning roles to service account..."
gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" --role="roles/iam.serviceAccountUser"
gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com" --role="roles/storage.admin"

# Deploy the SCIM Bridge on GCP Cloud Run
echo "Step 4: Deploying SCIM Bridge to Cloud Run..."
gcloud run deploy scim-bridge \
    --image=$SCIM_BRIDGE_IMAGE \
    --region=$REGION \
    --service-account=$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com \
    --allow-unauthenticated

# Get the URL of the deployed SCIM Bridge
SCIM_BRIDGE_URL=$(gcloud run services describe scim-bridge --region=$REGION --format 'value(status.url)')
echo "SCIM Bridge deployed successfully at $SCIM_BRIDGE_URL"

# Create configuration file for 1Password SCIM Bridge
echo "Step 5: Creating SCIM Bridge configuration..."
mkdir -p 1password-scim-config
cat > 1password-scim-config/scimsession <<EOF
{
  "bridge": {
    "bridge_url": "$SCIM_BRIDGE_URL"
  },
  "google": {
    "admin_email": "$ADMIN_EMAIL",
    "domain": "$DOMAIN"
  }
}
EOF

echo "Step 6: Installing Google API dependencies..."
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib

# Instructions for manual steps
echo ""
echo "==== MANUAL CONFIGURATION REQUIRED ===="
echo "Please complete the following steps to finish the 1Password SSO setup:"
echo ""
echo "1. Create a Service Account Key in GCP:"
echo "   gcloud iam service-accounts keys create key.json --iam-account=$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"
echo ""
echo "2. In the Google Workspace Admin Console (https://admin.google.com):"
echo "   a. Go to Apps > Web and mobile apps > Add app > Add custom SAML app"
echo "   b. Configure the SAML app with the following details:"
echo "      - ACS URL: $SCIM_BRIDGE_URL/sso/acs"
echo "      - Entity ID: https://1password.com/sso"
echo "      - Name ID format: EMAIL"
echo "      - Name ID: Basic Information > Primary Email"
echo ""
echo "3. In the 1Password Admin Console:"
echo "   a. Go to People > Directory Sync > Set up directory sync"
echo "   b. Configure the SCIM Bridge with the URL: $SCIM_BRIDGE_URL"
echo "   c. Set up the SSO integration with Google Workspace"
echo ""
echo "Configuration Summary:"
echo "- SCIM Bridge URL: $SCIM_BRIDGE_URL"
echo "- Google Workspace Domain: $DOMAIN"
echo "- Admin Email: $ADMIN_EMAIL"
echo ""
echo "For more details, refer to the 1Password documentation:"
echo "https://support.1password.com/scim-google-workspace/"
echo "https://support.1password.com/sso-configure/"