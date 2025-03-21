"""
ZeroBounce Email Verification Service
API Documentation: https://www.zerobounce.net/services/
"""
import os
import requests
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ZeroBounceService:
    """Service class for ZeroBounce email verification."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize ZeroBounce service with API key."""
        self.api_key = api_key or os.getenv("ZEROBOUNCE_API_KEY")
        self.base_url = "https://api.zerobounce.net/v2"
        
        if not self.api_key:
            logger.warning("ZeroBounce API key not provided. Service will not function.")
    
    def verify_email(self, email: str) -> Dict[str, Any]:
        """
        Verify an email address using ZeroBounce API.
        
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
                "provider": "zerobounce"
            }
        
        endpoint = f"{self.base_url}/validate"
        params = {
            "api_key": self.api_key,
            "email": email,
            "ip_address": ""  # Optional parameter
        }
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Process response
            status = data.get("status")
            is_valid = status == "valid"
            
            return {
                "email": email,
                "is_valid": is_valid,
                "score": 1.0 if is_valid else 0.0,
                "provider": "zerobounce",
                "details": data
            }
        except Exception as e:
            logger.error(f"Error verifying email with ZeroBounce: {str(e)}")
            return {
                "email": email,
                "is_valid": None,
                "error": str(e),
                "provider": "zerobounce"
            }
    
    def get_credits(self) -> Dict[str, Any]:
        """Get the number of credits remaining in the account."""
        if not self.api_key:
            return {"error": "API key not provided"}
        
        endpoint = f"{self.base_url}/getcredits"
        params = {"api_key": self.api_key}
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting ZeroBounce credits: {str(e)}")
            return {"error": str(e)}
    
    def bulk_verify(self, emails: list) -> Dict[str, Any]:
        """
        Submit a bulk email verification request.
        
        Args:
            emails: List of email addresses to verify
            
        Returns:
            Dict with file_id for status checking
        """
        if not self.api_key:
            return {"error": "API key not provided"}
        
        endpoint = f"{self.base_url}/bulkvalidation"
        
        # Prepare the data for bulk validation
        # This is simplified - in production you would need to handle file uploads
        data = {
            "api_key": self.api_key,
            "email_batch": emails
        }
        
        try:
            response = requests.post(endpoint, json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error submitting bulk verification to ZeroBounce: {str(e)}")
            return {"error": str(e)}
    
    def check_bulk_status(self, file_id: str) -> Dict[str, Any]:
        """
        Check the status of a bulk email verification request.
        
        Args:
            file_id: The file ID returned from bulk_verify
            
        Returns:
            Dict with status information
        """
        if not self.api_key:
            return {"error": "API key not provided"}
        
        endpoint = f"{self.base_url}/getfile"
        params = {
            "api_key": self.api_key,
            "file_id": file_id
        }
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error checking bulk status on ZeroBounce: {str(e)}")
            return {"error": str(e)}