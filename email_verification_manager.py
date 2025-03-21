"""
Email Verification Manager

This module provides a centralized manager for all email verification services.
It handles service selection, verification requests, and result aggregation.
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy.orm import Session

from database import EmailVerification, get_db
from services import (
    ZeroBounceService,
    MailboxLayerService,
    NeutrinoAPIService,
    SpokeoService,
    HunterService
)

logger = logging.getLogger(__name__)

class EmailVerificationManager:
    """Manager class for handling multiple email verification services."""
    
    def __init__(self):
        """Initialize the verification manager with all available services."""
        self.services = {
            "zerobounce": ZeroBounceService(),
            "mailboxlayer": MailboxLayerService(),
            "neutrinoapi": NeutrinoAPIService(),
            "spokeo": SpokeoService(),
            "hunter": HunterService()
        }
        
        # Log which services have API keys configured
        for service_name, service in self.services.items():
            if hasattr(service, 'api_key') and service.api_key:
                logger.info(f"{service_name} API key is configured")
            else:
                logger.warning(f"{service_name} API key is not configured")
    
    def get_available_services(self) -> List[str]:
        """Get a list of service names that have API keys configured."""
        return [
            name for name, service in self.services.items()
            if hasattr(service, 'api_key') and service.api_key
        ]
    
    def verify_email(self, email: str, service_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Verify an email using either a specific service or all available services.
        
        Args:
            email: The email address to verify
            service_name: The specific service to use (optional)
            
        Returns:
            Dict with verification results
        """
        if service_name:
            if service_name not in self.services:
                return {
                    "email": email,
                    "error": f"Service '{service_name}' not found",
                    "verified": False
                }
            
            service = self.services[service_name]
            result = service.verify_email(email)
            self._store_verification_result(result)
            return result
        else:
            # Use all available services and combine results
            available_services = self.get_available_services()
            if not available_services:
                return {
                    "email": email,
                    "error": "No verification services are configured with API keys",
                    "verified": False
                }
            
            results = {}
            valid_count = 0
            total_score = 0.0
            service_count = 0
            
            # Verify with all available services
            with ThreadPoolExecutor(max_workers=len(available_services)) as executor:
                future_to_service = {
                    executor.submit(self.services[name].verify_email, email): name
                    for name in available_services
                }
                
                for future in as_completed(future_to_service):
                    service_name = future_to_service[future]
                    try:
                        service_result = future.result()
                        results[service_name] = service_result
                        
                        # Store result in database
                        self._store_verification_result(service_result)
                        
                        # Count valid results and accumulate scores
                        if service_result.get("is_valid"):
                            valid_count += 1
                        
                        if service_result.get("score") is not None:
                            total_score += service_result.get("score", 0.0)
                            service_count += 1
                    except Exception as e:
                        logger.error(f"Error getting result from {service_name}: {str(e)}")
                        results[service_name] = {
                            "email": email,
                            "error": str(e),
                            "provider": service_name
                        }
            
            # Determine aggregate validity and score
            is_valid = None
            if valid_count > 0:
                is_valid = valid_count >= len(available_services) / 2  # Simple majority
            
            aggregate_score = None
            if service_count > 0:
                aggregate_score = total_score / service_count
            
            return {
                "email": email,
                "is_valid": is_valid,
                "score": aggregate_score,
                "results": results,
                "verified_by": len(results),
                "verification_date": datetime.utcnow().isoformat()
            }
    
    def bulk_verify(self, emails: List[str], service_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Verify multiple email addresses.
        
        Args:
            emails: List of email addresses to verify
            service_name: The specific service to use (optional)
            
        Returns:
            Dict with verification results for each email
        """
        if not emails:
            return {"error": "No emails provided"}
        
        if service_name:
            if service_name not in self.services:
                return {"error": f"Service '{service_name}' not found"}
            
            service = self.services[service_name]
            if hasattr(service, 'bulk_verify'):
                return service.bulk_verify(emails)
            else:
                # Fall back to individual verification
                results = []
                for email in emails:
                    results.append(service.verify_email(email))
                return {"results": results}
        else:
            # Use individual verification with all services for each email
            results = []
            for email in emails:
                results.append(self.verify_email(email))
            return {"results": results}
    
    def get_verification_history(self, email: str) -> List[Dict[str, Any]]:
        """
        Get verification history for an email from the database.
        
        Args:
            email: The email address to get history for
            
        Returns:
            List of verification records
        """
        results = []
        session = next(get_db())
        
        try:
            verifications = session.query(EmailVerification).filter(
                EmailVerification.email == email
            ).order_by(EmailVerification.verification_date.desc()).all()
            
            results = [v.to_dict() for v in verifications]
        except Exception as e:
            logger.error(f"Error getting verification history: {str(e)}")
        finally:
            session.close()
        
        return results
    
    def _store_verification_result(self, result: Dict[str, Any]) -> None:
        """
        Store a verification result in the database.
        
        Args:
            result: The verification result to store
        """
        if not result or "email" not in result:
            return
        
        try:
            session = next(get_db())
            
            verification = EmailVerification(
                email=result.get("email"),
                is_valid=result.get("is_valid"),
                score=result.get("score"),
                provider=result.get("provider"),
                details=result.get("details")
            )
            
            session.add(verification)
            session.commit()
            session.close()
        except Exception as e:
            logger.error(f"Error storing verification result: {str(e)}")