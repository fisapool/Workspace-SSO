"""
MailboxLayer Email Verification Service
API Documentation: https://mailboxlayer.com/documentation
"""
import os
import requests
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class MailboxLayerService:
    """Service class for MailboxLayer email verification."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize MailboxLayer service with API key."""
        self.api_key = api_key or os.getenv("MAILBOXLAYER_API_KEY")
        self.base_url = "https://api.mailboxlayer.com"
        
        if not self.api_key:
            logger.warning("MailboxLayer API key not provided. Service will not function.")
    
    def verify_email(self, email: str) -> Dict[str, Any]:
        """
        Verify an email address using MailboxLayer API.
        
        Args:
            email: The email address to verify
            
        Returns:
            Dict with verification results
        """
        if not self.api_key:
            return {
                "email": email,
                "is_valid": None,
                "error": "API key not provided",
                "provider": "mailboxlayer"
            }
        
        endpoint = f"{self.base_url}/check"
        params = {
            "access_key": self.api_key,
            "email": email,
            "smtp": 1,
            "format": 1
        }
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Check if the response contains error information
            if "error" in data:
                raise Exception(data["error"]["info"])
            
            # Process response
            # MailboxLayer considers an email valid if format_valid, mx_found, and smtp_check are true
            is_valid = all([
                data.get("format_valid", False),
                data.get("mx_found", False),
                data.get("smtp_check", False)
            ])
            
            # Calculate score based on various checks
            score_factors = [
                data.get("format_valid", False),
                data.get("mx_found", False),
                data.get("smtp_check", False),
                not data.get("disposable", True),
                not data.get("free", True) if "free" in data else True
            ]
            score = sum(1 for factor in score_factors if factor) / len(score_factors)
            
            return {
                "email": email,
                "is_valid": is_valid,
                "score": score,
                "provider": "mailboxlayer",
                "details": data
            }
        except Exception as e:
            logger.error(f"Error verifying email with MailboxLayer: {str(e)}")
            return {
                "email": email,
                "is_valid": None,
                "error": str(e),
                "provider": "mailboxlayer"
            }
    
    def bulk_verify(self, emails: list) -> Dict[str, list]:
        """
        Verify multiple email addresses.
        Note: MailboxLayer doesn't support bulk verification directly, so we process one by one.
        
        Args:
            emails: List of email addresses to verify
            
        Returns:
            Dict with results for each email
        """
        if not self.api_key:
            return {"error": "API key not provided"}
        
        results = []
        for email in emails:
            results.append(self.verify_email(email))
        
        return {"results": results}