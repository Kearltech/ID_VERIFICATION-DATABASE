"""
Repository pattern for database operations
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import uuid
import json

from .models import User, Submission, ValidationLog, APIUsage, AuditLog


class UserRepository:
    """Repository for User operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, username: str, email: str, full_name: str = None, role: str = 'user') -> User:
        """Create a new user"""
        user = User(
            user_id=str(uuid.uuid4()),
            username=username,
            email=email,
            full_name=full_name,
            role=role
        )
        self.session.add(user)
        self.session.commit()
        return user
    
    def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.session.query(User).filter(User.user_id == user_id).first()
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.session.query(User).filter(User.username == username).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.session.query(User).filter(User.email == email).first()
    
    def get_all(self, active_only: bool = True) -> List[User]:
        """Get all users"""
        query = self.session.query(User)
        if active_only:
            query = query.filter(User.is_active == True)
        return query.all()
    
    def update_last_login(self, user_id: str):
        """Update user's last login timestamp"""
        user = self.get_by_id(user_id)
        if user:
            user.last_login = datetime.utcnow()
            self.session.commit()


class SubmissionRepository:
    """Repository for Submission operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, submission_data: Dict[str, Any]) -> Submission:
        """Create a new submission"""
        submission = Submission(
            submission_id=str(uuid.uuid4()),
            **submission_data
        )
        # Set automatic deletion date (90 days default)
        submission.set_deletion_date(90)
        
        self.session.add(submission)
        self.session.commit()
        return submission
    
    def get_by_id(self, submission_id: str) -> Optional[Submission]:
        """Get submission by ID"""
        return self.session.query(Submission).filter(
            Submission.submission_id == submission_id,
            Submission.is_deleted == False
        ).first()
    
    def get_by_user(self, user_id: str, limit: int = 100) -> List[Submission]:
        """Get user's submissions"""
        return self.session.query(Submission).filter(
            Submission.user_id == user_id,
            Submission.is_deleted == False
        ).order_by(Submission.created_at.desc()).limit(limit).all()
    
    def get_recent(self, days: int = 7, limit: int = 100) -> List[Submission]:
        """Get recent submissions"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return self.session.query(Submission).filter(
            Submission.created_at >= cutoff_date,
            Submission.is_deleted == False
        ).order_by(Submission.created_at.desc()).limit(limit).all()
    
    def update(self, submission_id: str, updates: Dict[str, Any]) -> Optional[Submission]:
        """Update submission"""
        submission = self.get_by_id(submission_id)
        if submission:
            for key, value in updates.items():
                setattr(submission, key, value)
            submission.updated_at = datetime.utcnow()
            self.session.commit()
        return submission
    
    def soft_delete(self, submission_id: str) -> bool:
        """Soft delete a submission"""
        submission = self.get_by_id(submission_id)
        if submission:
            submission.is_deleted = True
            submission.updated_at = datetime.utcnow()
            self.session.commit()
            return True
        return False
    
    def get_statistics(self, user_id: str = None, days: int = 30) -> Dict[str, Any]:
        """Get validation statistics"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = self.session.query(Submission).filter(
            Submission.created_at >= cutoff_date,
            Submission.is_deleted == False
        )
        
        if user_id:
            query = query.filter(Submission.user_id == user_id)
        
        total = query.count()
        passed = query.filter(Submission.validation_overall == True).count()
        failed = total - passed
        
        # Get breakdown by ID type
        id_type_stats = self.session.query(
            Submission.id_type,
            func.count(Submission.id).label('count')
        ).filter(
            Submission.created_at >= cutoff_date,
            Submission.is_deleted == False
        )
        
        if user_id:
            id_type_stats = id_type_stats.filter(Submission.user_id == user_id)
        
        id_type_stats = id_type_stats.group_by(Submission.id_type).all()
        
        return {
            'total_submissions': total,
            'passed': passed,
            'failed': failed,
            'success_rate': round((passed / total * 100) if total > 0 else 0, 2),
            'period_days': days,
            'id_type_breakdown': {id_type: count for id_type, count in id_type_stats}
        }


class ValidationLogRepository:
    """Repository for ValidationLog operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, submission_id: str, field_name: str, validation_type: str, 
               validation_result: bool, **kwargs) -> ValidationLog:
        """Create a validation log entry"""
        log = ValidationLog(
            log_id=str(uuid.uuid4()),
            submission_id=submission_id,
            field_name=field_name,
            validation_type=validation_type,
            validation_result=validation_result,
            **kwargs
        )
        self.session.add(log)
        self.session.commit()
        return log
    
    def get_by_submission(self, submission_id: str) -> List[ValidationLog]:
        """Get all validation logs for a submission"""
        return self.session.query(ValidationLog).filter(
            ValidationLog.submission_id == submission_id
        ).order_by(ValidationLog.validated_at).all()
    
    def get_failed_validations(self, days: int = 7) -> List[ValidationLog]:
        """Get failed validations"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return self.session.query(ValidationLog).filter(
            ValidationLog.validated_at >= cutoff_date,
            ValidationLog.validation_result == False
        ).all()


class APIUsageRepository:
    """Repository for API usage tracking"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def log_usage(self, user_id: str, api_operation: str, model_name: str,
                  input_tokens: int, output_tokens: int, estimated_cost: float,
                  success: bool = True, **kwargs) -> APIUsage:
        """Log API usage"""
        usage = APIUsage(
            usage_id=str(uuid.uuid4()),
            user_id=user_id,
            api_operation=api_operation,
            model_name=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            estimated_cost_usd=estimated_cost,
            success=success,
            **kwargs
        )
        self.session.add(usage)
        self.session.commit()
        return usage
    
    def get_user_usage(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get user's API usage statistics"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        usage_records = self.session.query(APIUsage).filter(
            APIUsage.user_id == user_id,
            APIUsage.created_at >= cutoff_date
        ).all()
        
        total_cost = sum(record.estimated_cost_usd or 0 for record in usage_records)
        total_tokens = sum(record.total_tokens or 0 for record in usage_records)
        total_calls = len(usage_records)
        successful_calls = sum(1 for record in usage_records if record.success)
        
        return {
            'user_id': user_id,
            'period_days': days,
            'total_api_calls': total_calls,
            'successful_calls': successful_calls,
            'failed_calls': total_calls - successful_calls,
            'total_tokens': total_tokens,
            'total_cost_usd': round(total_cost, 4),
            'success_rate': round((successful_calls / total_calls * 100) if total_calls > 0 else 0, 2)
        }
    
    def get_total_usage(self, days: int = 30) -> Dict[str, Any]:
        """Get total system API usage"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        total_cost = self.session.query(func.sum(APIUsage.estimated_cost_usd)).filter(
            APIUsage.created_at >= cutoff_date
        ).scalar() or 0
        
        total_tokens = self.session.query(func.sum(APIUsage.total_tokens)).filter(
            APIUsage.created_at >= cutoff_date
        ).scalar() or 0
        
        total_calls = self.session.query(func.count(APIUsage.id)).filter(
            APIUsage.created_at >= cutoff_date
        ).scalar()
        
        return {
            'period_days': days,
            'total_api_calls': total_calls,
            'total_tokens': total_tokens,
            'total_cost_usd': round(total_cost, 4)
        }


class AuditLogRepository:
    """Repository for audit log operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def log_event(self, event_type: str, event_category: str, event_description: str,
                  user_id: str = None, severity: str = 'info', **kwargs) -> AuditLog:
        """Log an audit event"""
        log = AuditLog(
            log_id=str(uuid.uuid4()),
            event_type=event_type,
            event_category=event_category,
            event_description=event_description,
            user_id=user_id,
            severity=severity,
            event_data=json.dumps(kwargs.get('event_data', {})),
            **{k: v for k, v in kwargs.items() if k != 'event_data'}
        )
        self.session.add(log)
        self.session.commit()
        return log
    
    def get_recent_logs(self, limit: int = 100, severity: str = None) -> List[AuditLog]:
        """Get recent audit logs"""
        query = self.session.query(AuditLog)
        if severity:
            query = query.filter(AuditLog.severity == severity)
        return query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    
    def get_user_logs(self, user_id: str, days: int = 30) -> List[AuditLog]:
        """Get user's audit logs"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return self.session.query(AuditLog).filter(
            AuditLog.user_id == user_id,
            AuditLog.created_at >= cutoff_date
        ).order_by(AuditLog.created_at.desc()).all()
