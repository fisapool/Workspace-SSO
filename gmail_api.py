import os
import base64
import re
import email
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
import pandas as pd
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import streamlit as st

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def authenticate_gmail():
    """Authenticate with Gmail API using OAuth2."""
    creds = None
    
    # Check if we have valid credentials saved
    token_info = st.session_state.get('token_info', None)
    if token_info:
        creds = Credentials(
            token=token_info.get('token'),
            refresh_token=token_info.get('refresh_token'),
            token_uri=token_info.get('token_uri'),
            client_id=token_info.get('client_id'),
            client_secret=token_info.get('client_secret'),
            scopes=token_info.get('scopes')
        )
    
    # If there are no valid credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Use streamlit-specific OAuth flow
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
                SCOPES
            )
            creds = flow.run_local_server(port=8501)
            
            # Save credentials for future use
            st.session_state['token_info'] = {
                'token': creds.token,
                'refresh_token': creds.refresh_token,
                'token_uri': creds.token_uri,
                'client_id': creds.client_id,
                'client_secret': creds.client_secret,
                'scopes': creds.scopes
            }
    
    return creds

def get_gmail_service(creds):
    """Build and return the Gmail API service."""
    return build('gmail', 'v1', credentials=creds)

def get_messages(service, max_results=500, query=""):
    """Get messages from Gmail API."""
    try:
        results = service.users().messages().list(
            userId='me',
            maxResults=max_results,
            q=query
        ).execute()
        
        messages = results.get('messages', [])
        
        # Keep getting messages if there are more
        next_page_token = results.get('nextPageToken')
        while next_page_token and len(messages) < max_results:
            results = service.users().messages().list(
                userId='me',
                maxResults=max_results - len(messages),
                pageToken=next_page_token,
                q=query
            ).execute()
            
            messages.extend(results.get('messages', []))
            next_page_token = results.get('nextPageToken')
        
        return messages
    except Exception as e:
        st.error(f"Error retrieving messages: {str(e)}")
        return []

def get_message_detail(service, msg_id):
    """Get detailed information for a specific message."""
    try:
        message = service.users().messages().get(
            userId='me',
            id=msg_id,
            format='full'
        ).execute()
        
        return message
    except Exception as e:
        st.error(f"Error retrieving message details: {str(e)}")
        return None

def parse_message_payload(payload):
    """Parse the message payload to extract subject and body."""
    headers = payload.get('headers', [])
    
    # Extract header fields
    subject = ""
    from_email = ""
    to_email = ""
    date_str = ""
    
    for header in headers:
        name = header.get('name', '').lower()
        value = header.get('value', '')
        
        if name == 'subject':
            subject = value
        elif name == 'from':
            from_email = extract_email(value)
        elif name == 'to':
            to_email = extract_email(value)
        elif name == 'date':
            date_str = value
    
    # Parse body
    body = ""
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                body_data = part['body'].get('data', '')
                if body_data:
                    body += base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
            elif 'parts' in part:
                for subpart in part['parts']:
                    if subpart['mimeType'] == 'text/plain':
                        body_data = subpart['body'].get('data', '')
                        if body_data:
                            body += base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
    elif 'body' in payload and 'data' in payload['body']:
        body_data = payload['body']['data']
        body = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
    
    # Parse date
    date = None
    if date_str:
        try:
            date = parsedate_to_datetime(date_str)
        except Exception:
            # Fallback to current time if date parsing fails
            date = datetime.now(timezone.utc)
    
    return {
        'subject': subject,
        'from': from_email,
        'to': to_email,
        'date': date,
        'body': body[:1000]  # Limit body to first 1000 chars to avoid huge dataframes
    }

def extract_email(header_value):
    """Extract email address from a header value that might include a name."""
    match = re.search(r'<(.+?)>', header_value)
    if match:
        return match.group(1).lower()
    return header_value.lower()

def extract_message_thread_id(message):
    """Extract thread ID from a message."""
    return message.get('threadId', '')

def extract_message_id(message):
    """Extract message ID from a message."""
    return message.get('id', '')

def extract_in_reply_to(payload):
    """Extract In-Reply-To header from payload."""
    headers = payload.get('headers', [])
    for header in headers:
        if header.get('name', '').lower() == 'in-reply-to':
            return header.get('value', '')
    return None

def extract_message_id_header(payload):
    """Extract Message-ID header from payload."""
    headers = payload.get('headers', [])
    for header in headers:
        if header.get('name', '').lower() == 'message-id':
            return header.get('value', '')
    return None
