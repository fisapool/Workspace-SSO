
from typing import Dict, Optional
import streamlit as st
from datetime import datetime, timedelta
import json

class CookieManager:
    def __init__(self):
        if 'cookies' not in st.session_state:
            st.session_state.cookies = {}
        self.default_expiry_days = 30

    def set_cookie_with_options(self, name: str, value: str, options: Dict = None) -> None:
        """Set a cookie with custom options."""
        if options is None:
            options = {}
        
        expiry = datetime.now() + timedelta(days=options.get('expires_days', self.default_expiry_days))
        st.session_state.cookies[name] = {
            'value': value,
            'expires': expiry.isoformat(),
            'path': options.get('path', '/'),
            'secure': options.get('secure', True),
            'httponly': options.get('httponly', True)
        }

    def get_cookie_details(self, name: str) -> Optional[Dict]:
        """Get full cookie details if it exists and hasn't expired."""
        if name in st.session_state.cookies:
            cookie = st.session_state.cookies[name]
            expiry = datetime.fromisoformat(cookie['expires'])
            if datetime.now() < expiry:
                return cookie
            else:
                del st.session_state.cookies[name]
        return None

    def has_cookie(self, name: str) -> bool:
        """Check if a valid cookie exists."""
        return self.get_cookie(name) is not None

    def extend_expiry(self, name: str, days: int = None) -> bool:
        """Extend the expiry of a cookie."""
        if name in st.session_state.cookies:
            days = days or self.default_expiry_days
            cookie = st.session_state.cookies[name]
            expiry = datetime.now() + timedelta(days=days)
            cookie['expires'] = expiry.isoformat()
            return True
        return False

    def set_cookie(self, name: str, value: str, expires_days: int = 30) -> None:
        """Set a cookie with expiration."""
        expiry = datetime.now() + timedelta(days=expires_days)
        st.session_state.cookies[name] = {
            'value': value,
            'expires': expiry.isoformat()
        }

    def get_cookie(self, name: str) -> Optional[str]:
        """Get cookie value if it exists and hasn't expired."""
        if name in st.session_state.cookies:
            cookie = st.session_state.cookies[name]
            expiry = datetime.fromisoformat(cookie['expires'])
            if datetime.now() < expiry:
                return cookie['value']
            else:
                del st.session_state.cookies[name]
        return None

    def delete_cookie(self, name: str) -> None:
        """Delete a cookie if it exists."""
        if name in st.session_state.cookies:
            del st.session_state.cookies[name]

    def get_all_cookies(self) -> Dict:
        """Get all valid cookies."""
        valid_cookies = {}
        now = datetime.now()
        for name, cookie in st.session_state.cookies.items():
            expiry = datetime.fromisoformat(cookie['expires'])
            if now < expiry:
                valid_cookies[name] = cookie['value']
        return valid_cookies

    def clear_all_cookies(self) -> None:
        """Clear all cookies."""
        st.session_state.cookies = {}
