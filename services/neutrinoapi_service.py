"""
NeutrinoAPI Email Verification Service
API Documentation: https://www.neutrinoapi.com/api/api-basics/
"""
import os
import requests
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class NeutrinoAPIService:
    """Service class for NeutrinoAPI email verification."""
    
    def __init__(self, user_id: Optional[str] = None, api_key: Optional[str] = None):
        """Initialize NeutrinoAPI service with credentials."""
        self.user_id = user_id or os.getenv("NEUTRINOAPI_USER_ID")
        self.api_key = api_key or os.getenv("NEUTRINOAPI_API_KEY")
        self.base_url = "https://neutrinoapi.net"
        
        if not (self.api_key and self.user_id):
            logger.warning("NeutrinoAPI credentials not provided. Service will not function.")
    
    def verify_email(self, email: str) -> Dict[str, Any]:
        """
        Verify an email address using NeutrinoAPI.
        
        Args:
            email: The email address to verify
            
        Returns:
            Dict with verification results
        """
        if not (self.api_key and self.user_id):
            return {
                "email": email,
                "is_valid": None,
                "error": "API credentials not provided",
                "provider": "neutrinoapi"
            }
        
        endpoint = f"{self.base_url}/email-validate"
        headers = {
            "User-ID": self.user_id,
            "API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        data = {"email": email}
        
        try:
            response = requests.post(endpoint, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            # Process response
            is_valid = result.get("valid", False)
            
            # Calculate a score based on the verification results
            score_factors = [
                result.get("valid", False),
                result.get("syntax.valid", False),
                not result.get("disposable", True),
                result.get("domain.exists", False),
                result.get("domain.has-mx", False),
                not result.get("is-freemail", True) if "is-freemail" in result else True
            ]
            score = sum(1 for factor in score_factors if factor) / len(score_factors)
            
            return {
                "email": email,
                "is_valid": is_valid,
                "score": score,
                "provider": "neutrinoapi",
                "details": result
            }
        except Exception as e:
            logger.error(f"Error verifying email with NeutrinoAPI: {str(e)}")
            return {
                "email": email,
                "is_valid": None,
                "error": str(e),
                "provider": "neutrinoapi"
            }
    
    def email_validation_and_verification(self, email: str) -> Dict[str, Any]:
        """
        Expanded email verification with validation of syntax, domain, and more.
        
        Args:
            email: The email address to verify
            
        Returns:
            Dict with detailed verification results
        """
        return self.verify_email(email)
    
    def bulk_verify(self, emails: list) -> Dict[str, list]:
        """
        Verify multiple email addresses.
        Note: NeutrinoAPI doesn't have a specific bulk endpoint, so we process one by one.
        
        Args:
            emails: List of email addresses to verify
            
        Returns:
            Dict with results for each email
        """
        if not (self.api_key and self.user_id):
            return {"error": "API credentials not provided"}
        
        results = []
        for email in emails:
            results.append(self.verify_email(email))
        
        return {"results": results}