"""
Database utilities for ID Verification System
"""
from typing import Dict, Any, Optional
from datetime import datetime
import json
from cryptography.fernet import Fernet
import os
import base64

from database.connection import get_db_session
from database.repository import (
    SubmissionRepository,
    UserRepository,
    ValidationLogRepository,
    APIUsageRepository,
    AuditLogRepository
)


class EncryptionManager:
    """Manages encryption/decryption of sensitive data"""
    
    def __init__(self, key: bytes = None):
        """
        Initialize encryption manager
        
        Args:
            key: Encryption key (generates new if not provided)
        """
        if key is None:
            # Try to get key from environment
            key_str = os.getenv('ENCRYPTION_KEY')
            if key_str:
                key = base64.urlsafe_b64decode(key_str)
            else:
                key = Fernet.generate_key()
        
        self.cipher = Fernet(key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data"""
        if not data:
            return ""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        if not encrypted_data:
            return ""
        return self.cipher.decrypt(encrypted_data.encode()).decode()
    
    @staticmethod
    def generate_key() -> str:
        """Generate a new encryption key"""
        return Fernet.generate_key().decode()


class DatabaseService:
    """High-level database service for the application"""
    
    def __init__(self, encrypt_sensitive_data: bool = True):
        self.encryption = EncryptionManager() if encrypt_sensitive_data else None
    
    def save_submission(
        self,
        user_id: str,
        id_type: str,
        form_data: Dict[str, Any],
        validation_results: Dict[str, Any],
        ocr_results: Dict[str, Any] = None,
        face_match_results: Dict[str, Any] = None,
        gemini_results: Dict[str, Any] = None,
        file_paths: Dict[str, str] = None
    ) -> str:
        """
        Save a verification submission to the database
        
        Args:
            user_id: User ID
            id_type: Type of ID (Ghana Card, Passport, etc.)
            form_data: User input form data
            validation_results: Validation results
            ocr_results: OCR comparison results
            face_match_results: Face matching results
            gemini_results: Gemini API results
            file_paths: Uploaded file paths
        
        Returns:
            submission_id: Unique submission ID
        """
        with get_db_session() as session:
            submission_repo = SubmissionRepository(session)
            user_repo = UserRepository(session)
            
            # Ensure user exists (avoid FK errors)
            user_record = user_repo.get_by_id(user_id)
            if not user_record:
                # Fall back to username-based lookup/create
                username = user_id or 'default_user'
                email = f"{username}@idverification.local"
                user_record = user_repo.get_by_username(username)
                if not user_record:
                    user_record = user_repo.create(username=username, email=email, full_name='Default User')
            user_id = user_record.user_id
            
            # Prepare submission data
            submission_data = {
                'user_id': user_id,
                'id_type': id_type,
                'sex': form_data.get('sex'),
                'issuing_country': form_data.get('issuing_country'),
                'validation_overall': validation_results.get('overall', False),
                'validation_details': json.dumps(validation_results)
            }
            
            # Encrypt sensitive fields
            if self.encryption:
                if 'id_number' in form_data:
                    submission_data['id_number_encrypted'] = self.encryption.encrypt(
                        str(form_data.get('id_number', ''))
                    )
                if 'surname' in form_data:
                    submission_data['surname_encrypted'] = self.encryption.encrypt(
                        str(form_data.get('surname', ''))
                    )
                if 'firstname' in form_data:
                    submission_data['firstname_encrypted'] = self.encryption.encrypt(
                        str(form_data.get('firstname', ''))
                    )
                if 'date_of_birth' in form_data:
                    submission_data['date_of_birth_encrypted'] = self.encryption.encrypt(
                        str(form_data.get('date_of_birth', ''))
                    )
            
            # Add face match results
            if face_match_results:
                submission_data['face_match'] = face_match_results.get('match', False)
                submission_data['face_match_distance'] = face_match_results.get('distance')
            
            # Add OCR comparison results
            if ocr_results:
                submission_data['ocr_comparison_result'] = ocr_results.get('valid', False)
                matched = len(ocr_results.get('passed_fields', []))
                total = matched + len(ocr_results.get('failed_fields', []))
                submission_data['ocr_match_percentage'] = (matched / total * 100) if total > 0 else 0
            
            # Add Gemini results
            if gemini_results:
                submission_data['gemini_card_type'] = gemini_results.get('card_type')
                submission_data['gemini_confidence'] = gemini_results.get('confidence')
                submission_data['gemini_extracted_fields'] = json.dumps(
                    gemini_results.get('text_fields', {})
                )
            
            # Add file paths
            if file_paths:
                submission_data['portrait_file_path'] = file_paths.get('portrait')
                submission_data['id_card_file_path'] = file_paths.get('id_card')
            
            # Create submission
            submission = repo.create(submission_data)
            return submission.submission_id
    
    def save_validation_logs(
        self,
        submission_id: str,
        field_results: Dict[str, Dict[str, Any]]
    ):
        """
        Save detailed validation logs
        
        Args:
            submission_id: Submission ID
            field_results: Dictionary of field validation results
        """
        with get_db_session() as session:
            repo = ValidationLogRepository(session)
            
            for field_name, result in field_results.items():
                repo.create(
                    submission_id=submission_id,
                    field_name=field_name,
                    validation_type=result.get('type', 'format'),
                    validation_result=result.get('pass', False),
                    expected_value=str(result.get('expected')),
                    actual_value=str(result.get('actual')),
                    error_message=result.get('msg')
                )
    
    def log_api_usage(
        self,
        user_id: str,
        api_operation: str,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        estimated_cost: float,
        success: bool = True,
        submission_id: str = None,
        duration_ms: int = None,
        error_message: str = None
    ):
        """Log API usage"""
        with get_db_session() as session:
            repo = APIUsageRepository(session)
            repo.log_usage(
                user_id=user_id,
                api_operation=api_operation,
                model_name=model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                estimated_cost=estimated_cost,
                success=success,
                submission_id=submission_id,
                request_duration_ms=duration_ms,
                error_message=error_message
            )
    
    def log_audit_event(
        self,
        event_type: str,
        event_category: str,
        description: str,
        user_id: str = None,
        severity: str = 'info',
        **kwargs
    ):
        """Log audit event"""
        with get_db_session() as session:
            repo = AuditLogRepository(session)
            repo.log_event(
                event_type=event_type,
                event_category=event_category,
                event_description=description,
                user_id=user_id,
                severity=severity,
                **kwargs
            )
    
    def get_user_statistics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get user's verification statistics"""
        with get_db_session() as session:
            submission_repo = SubmissionRepository(session)
            api_repo = APIUsageRepository(session)
            
            return {
                'submissions': submission_repo.get_statistics(user_id, days),
                'api_usage': api_repo.get_user_usage(user_id, days)
            }
    
    def get_user_submissions(self, user_id: str, limit: int = 100):
        """Get user's recent submissions"""
        with get_db_session() as session:
            repo = SubmissionRepository(session)
            submissions = repo.get_by_user(user_id, limit)
            
            # Decrypt sensitive data if needed
            if self.encryption:
                for submission in submissions:
                    if submission.id_number_encrypted:
                        submission.id_number = self.encryption.decrypt(
                            submission.id_number_encrypted
                        )
                    if submission.surname_encrypted:
                        submission.surname = self.encryption.decrypt(
                            submission.surname_encrypted
                        )
                    if submission.firstname_encrypted:
                        submission.firstname = self.encryption.decrypt(
                            submission.firstname_encrypted
                        )
            
            return submissions
    
    def create_user(
        self,
        username: str,
        email: str,
        full_name: str = None
    ) -> str:
        """Create a new user"""
        with get_db_session() as session:
            repo = UserRepository(session)
            user = repo.create(username, email, full_name)
            return user.user_id
    
    def get_or_create_user(
        self,
        username: str,
        email: str = None,
        full_name: str = None
    ) -> str:
        """Get existing user or create new one"""
        with get_db_session() as session:
            repo = UserRepository(session)
            
            # Try to get existing user
            user = repo.get_by_username(username)
            if user:
                return user.user_id
            
            # Create new user
            if not email:
                email = f"{username}@idverification.local"
            user = repo.create(username, email, full_name)
            return user.user_id


# Global database service instance
_db_service = None


def get_db_service(encrypt_sensitive_data: bool = True) -> DatabaseService:
    """Get global database service instance"""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService(encrypt_sensitive_data)
    return _db_service
