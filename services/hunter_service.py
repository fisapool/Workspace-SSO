"""
Hunter.io Email Verification Service
API Documentation: https://hunter.io/api-documentation
"""
import os
import requests
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class HunterService:
    """Service class for Hunter.io email verification and email finder."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Hunter.io service with API key."""
        self.api_key = api_key or os.getenv("HUNTER_API_KEY")
        self.base_url = "https://api.hunter.io/v2"
        
        if not self.api_key:
            logger.warning("Hunter.io API key not provided. Service will not function.")
    
    def verify_email(self, email: str) -> Dict[str, Any]:
        """
        Verify an email address using Hunter.io API.
        
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
                "provider": "hunter"
            }
        
        endpoint = f"{self.base_url}/email-verifier"
        params = {
            "email": email,
            "api_key": self.api_key
        }
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json().get("data", {})
            
            # Process response
            status = data.get("status")
            is_valid = status in ["valid", "webmail"]
            
            # Calculate score based on Hunter's own score and other factors
            hunter_score = data.get("score", 0)
            
            return {
                "email": email,
                "is_valid": is_valid,
                "score": hunter_score,
                "provider": "hunter",
                "details": data
            }
        except Exception as e:
            logger.error(f"Error verifying email with Hunter.io: {str(e)}")
            return {
                "email": email,
                "is_valid": None,
                "error": str(e),
                "provider": "hunter"
            }
    
    def email_finder(self, domain: str, first_name: str = None, last_name: str = None, company: str = None) -> Dict[str, Any]:
        """
        Find email addresses for a given domain and person.
        
        Args:
            domain: The domain to search for emails
            first_name: First name of the person (optional)
            last_name: Last name of the person (optional)
            company: Company name (optional)
            
        Returns:
            Dict with found email information
        """
        if not self.api_key:
            return {"error": "API key not provided"}
        
        endpoint = f"{self.base_url}/email-finder"
        params = {
            "domain": domain,
            "api_key": self.api_key
        }
        
        if first_name:
            params["first_name"] = first_name
        if last_name:
            params["last_name"] = last_name
        if company:
            params["company"] = company
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return response.json().get("data", {})
        except Exception as e:
            logger.error(f"Error finding emails with Hunter.io: {str(e)}")
            return {"error": str(e)}
    
    def domain_search(self, domain: str, limit: int = 10) -> Dict[str, Any]:
        """
        Find email addresses for a given domain.
        
        Args:
            domain: The domain to search for emails
            limit: Maximum number of results to return
            
        Returns:
            Dict with found email information
        """
        if not self.api_key:
            return {"error": "API key not provided"}
        
        endpoint = f"{self.base_url}/domain-search"
        params = {
            "domain": domain,
            "limit": limit,
            "api_key": self.api_key
        }
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return response.json().get("data", {})
        except Exception as e:
            logger.error(f"Error searching domain with Hunter.io: {str(e)}")
            return {"error": str(e)}
    
    def bulk_verify(self, emails: list) -> Dict[str, Any]:
        """
        Verify multiple email addresses.
        For Hunter.io, we need to use their specific bulk verification API.
        
        Args:
            emails: List of email addresses to verify
            
        Returns:
            Dict with verification status/ID
        """
        if not self.api_key:
            return {"error": "API key not provided"}
        
        # For Hunter.io, bulk verification typically requires:
        # 1. Upload a list (CSV file)
        # 2. Get a verification ID
        # 3. Check status
        # 4. Download results
        
        # This is a simplified implementation - in a production environment
        # you would need to handle file creation, uploading, and status checks
        
        endpoint = f"{self.base_url}/bulks/verification"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        try:
            # Note: In a real implementation, you would need to upload a CSV file
            # This is a placeholder for demonstration purposes
            response = requests.post(endpoint, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error submitting bulk verification to Hunter.io: {str(e)}")
            return {"error": str(e)}