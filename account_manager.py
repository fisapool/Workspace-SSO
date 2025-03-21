
from typing import Dict, List
import json
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import base64
import streamlit as st

class GmailAccountManager:
    def __init__(self):
        self.accounts: Dict[str, Credentials] = {}
        self.SCOPES = [
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/gmail.modify'
        ]

    def add_account(self, email: str) -> bool:
        """Add a new Gmail account using OAuth2."""
        try:
            flow = InstalledAppFlow.from_client_config(
                {
                    "installed": {
                        "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
                        "project_id": os.getenv("GOOGLE_PROJECT_ID", ""),
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET", ""),
                        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob"]
                    }
                },
                self.SCOPES
            )
            creds = flow.run_local_server(port=8501)
            self.accounts[email] = creds
            self._save_credentials(email, creds)
            return True
        except Exception as e:
            st.error(f"Failed to add account {email}: {str(e)}")
            return False

    def _save_credentials(self, email: str, creds: Credentials) -> None:
        """Save encrypted credentials in session state."""
        if creds and creds.valid:
            st.session_state[f'token_info_{email}'] = {
                'token': base64.b64encode(creds.token.encode()).decode(),
                'refresh_token': base64.b64encode(creds.refresh_token.encode()).decode(),
                'token_uri': creds.token_uri,
                'client_id': creds.client_id,
                'client_secret': creds.client_secret,
                'scopes': creds.scopes
            }

    def verify_smtp(self, email: str) -> bool:
        """Verify SMTP connection for account."""
        if email not in self.accounts:
            return False
        
        service = build('gmail', 'v1', credentials=self.accounts[email])
        try:
            # Test API connection
            service.users().getProfile(userId='me').execute()
            return True
        except Exception:
            return False

    def get_account_status(self, email: str) -> Dict:
        """Get account health and quota information."""
        if email not in self.accounts:
            return {'status': 'Not Connected'}
        
        service = build('gmail', 'v1', credentials=self.accounts[email])
        try:
            profile = service.users().getProfile(userId='me').execute()
            return {
                'status': 'Active',
                'messages_total': profile.get('messagesTotal', 0),
                'threads_total': profile.get('threadsTotal', 0),
                'history_id': profile.get('historyId', ''),
                'email_address': profile.get('emailAddress', email)
            }
        except Exception as e:
            return {'status': f'Error: {str(e)}'}

    def list_accounts(self) -> List[str]:
        """List all managed accounts."""
        return list(self.accounts.keys())
