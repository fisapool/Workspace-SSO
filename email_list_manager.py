"""
Email List Manager

This module provides functionality for managing email lists, including
creation, updates, and importing/exporting.
"""
import os
import csv
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from database import EmailList, EmailListEntry, get_db

logger = logging.getLogger(__name__)

class EmailListManager:
    """Manager class for handling email lists."""
    
    def create_list(self, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new email list.
        
        Args:
            name: Name of the list
            description: Optional description
            
        Returns:
            Dict with list information
        """
        try:
            session = next(get_db())
            
            # Check if a list with this name already exists
            existing = session.query(EmailList).filter(EmailList.name == name).first()
            if existing:
                session.close()
                return {
                    "error": f"List with name '{name}' already exists",
                    "list_id": existing.id
                }
            
            # Create the new list
            email_list = EmailList(
                name=name,
                description=description
            )
            
            session.add(email_list)
            session.commit()
            
            list_id = email_list.id
            session.close()
            
            return {
                "list_id": list_id,
                "name": name,
                "description": description,
                "created": True
            }
        except Exception as e:
            logger.error(f"Error creating email list: {str(e)}")
            return {"error": str(e)}
    
    def add_email_to_list(self, list_id: int, email: str, 
                         first_name: Optional[str] = None, 
                         last_name: Optional[str] = None,
                         company: Optional[str] = None,
                         position: Optional[str] = None) -> Dict[str, Any]:
        """
        Add an email to a list.
        
        Args:
            list_id: ID of the list to add to
            email: Email address to add
            first_name: First name (optional)
            last_name: Last name (optional)
            company: Company name (optional)
            position: Job position (optional)
            
        Returns:
            Dict with operation result
        """
        try:
            session = next(get_db())
            
            # Check if the list exists
            email_list = session.query(EmailList).filter(EmailList.id == list_id).first()
            if not email_list:
                session.close()
                return {"error": f"List with ID {list_id} not found"}
            
            # Check if email already exists in this list
            existing = session.query(EmailListEntry).filter(
                EmailListEntry.list_id == list_id,
                EmailListEntry.email == email
            ).first()
            
            if existing:
                # Update existing entry
                existing.first_name = first_name if first_name else existing.first_name
                existing.last_name = last_name if last_name else existing.last_name
                existing.company = company if company else existing.company
                existing.position = position if position else existing.position
                session.commit()
                session.close()
                
                return {
                    "email": email,
                    "list_id": list_id,
                    "updated": True
                }
            
            # Create new entry
            entry = EmailListEntry(
                list_id=list_id,
                email=email,
                first_name=first_name,
                last_name=last_name,
                company=company,
                position=position
            )
            
            session.add(entry)
            session.commit()
            session.close()
            
            return {
                "email": email,
                "list_id": list_id,
                "added": True
            }
        except Exception as e:
            logger.error(f"Error adding email to list: {str(e)}")
            return {"error": str(e)}
    
    def get_lists(self) -> List[Dict[str, Any]]:
        """
        Get all email lists.
        
        Returns:
            List of email lists with counts
        """
        results = []
        try:
            session = next(get_db())
            
            # Get all lists
            lists = session.query(EmailList).all()
            
            for email_list in lists:
                # Count entries in each list
                count = session.query(EmailListEntry).filter(
                    EmailListEntry.list_id == email_list.id
                ).count()
                
                results.append({
                    "list_id": email_list.id,
                    "name": email_list.name,
                    "description": email_list.description,
                    "email_count": count,
                    "created_at": email_list.created_at.isoformat() if email_list.created_at else None,
                    "updated_at": email_list.updated_at.isoformat() if email_list.updated_at else None
                })
            
            session.close()
        except Exception as e:
            logger.error(f"Error getting email lists: {str(e)}")
        
        return results
    
    def get_list_entries(self, list_id: int) -> List[Dict[str, Any]]:
        """
        Get all entries in an email list.
        
        Args:
            list_id: ID of the list to get entries from
            
        Returns:
            List of email entries
        """
        results = []
        try:
            session = next(get_db())
            
            # Check if the list exists
            email_list = session.query(EmailList).filter(EmailList.id == list_id).first()
            if not email_list:
                session.close()
                return []
            
            # Get all entries
            entries = session.query(EmailListEntry).filter(
                EmailListEntry.list_id == list_id
            ).all()
            
            for entry in entries:
                results.append({
                    "id": entry.id,
                    "email": entry.email,
                    "first_name": entry.first_name,
                    "last_name": entry.last_name,
                    "company": entry.company,
                    "position": entry.position,
                    "added_at": entry.added_at.isoformat() if entry.added_at else None
                })
            
            session.close()
        except Exception as e:
            logger.error(f"Error getting list entries: {str(e)}")
        
        return results
    
    def import_from_csv(self, list_id: int, file_path: str) -> Dict[str, Any]:
        """
        Import emails into a list from a CSV file.
        
        Args:
            list_id: ID of the list to import into
            file_path: Path to the CSV file
            
        Returns:
            Dict with import results
        """
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}
        
        session = next(get_db())
        
        # Check if the list exists
        email_list = session.query(EmailList).filter(EmailList.id == list_id).first()
        if not email_list:
            session.close()
            return {"error": f"List with ID {list_id} not found"}
        
        try:
            added = 0
            updated = 0
            errors = 0
            
            with open(file_path, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row in reader:
                    email = row.get('email')
                    if not email:
                        errors += 1
                        continue
                    
                    result = self.add_email_to_list(
                        list_id=list_id,
                        email=email,
                        first_name=row.get('first_name'),
                        last_name=row.get('last_name'),
                        company=row.get('company'),
                        position=row.get('position')
                    )
                    
                    if 'error' in result:
                        errors += 1
                    elif result.get('added', False):
                        added += 1
                    elif result.get('updated', False):
                        updated += 1
            
            return {
                "list_id": list_id,
                "added": added,
                "updated": updated,
                "errors": errors,
                "file": file_path
            }
        except Exception as e:
            logger.error(f"Error importing from CSV: {str(e)}")
            return {"error": str(e)}
        finally:
            session.close()
    
    def export_to_csv(self, list_id: int, file_path: str) -> Dict[str, Any]:
        """
        Export email list to a CSV file.
        
        Args:
            list_id: ID of the list to export
            file_path: Path for the output CSV file
            
        Returns:
            Dict with export results
        """
        entries = self.get_list_entries(list_id)
        
        if not entries:
            return {
                "list_id": list_id,
                "exported": 0,
                "error": "No entries found or list doesn't exist"
            }
        
        try:
            with open(file_path, 'w', newline='') as csvfile:
                fieldnames = ['email', 'first_name', 'last_name', 'company', 'position', 'added_at']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for entry in entries:
                    writer.writerow({
                        'email': entry.get('email'),
                        'first_name': entry.get('first_name'),
                        'last_name': entry.get('last_name'),
                        'company': entry.get('company'),
                        'position': entry.get('position'),
                        'added_at': entry.get('added_at')
                    })
            
            return {
                "list_id": list_id,
                "exported": len(entries),
                "file": file_path
            }
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            return {"error": str(e)}