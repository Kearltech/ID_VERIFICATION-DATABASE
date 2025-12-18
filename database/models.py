"""
SQLAlchemy models for ID Verification System
"""
from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, Float, Boolean, Integer, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid

Base = declarative_base()


class User(Base):
    """User accounts table"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True)
    email = Column(String(255), unique=True, index=True)
    password_hash = Column(String(255))
    full_name = Column(String(200))
    role = Column(String(50), default='user')  # user, admin, verifier
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    last_login = Column(DateTime)
    
    # Relationships
    submissions = relationship("Submission", back_populates="user")
    api_usage = relationship("APIUsage", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"


class Submission(Base):
    """ID verification submissions table"""
    __tablename__ = 'submissions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    submission_id = Column(String(50), unique=True, index=True, nullable=False)
    user_id = Column(String(50), ForeignKey('users.user_id'), index=True)
    
    # ID Information (encrypted sensitive data)
    id_type = Column(String(50), index=True)
    id_number_encrypted = Column(Text)
    surname_encrypted = Column(Text)
    firstname_encrypted = Column(Text)
    date_of_birth_encrypted = Column(Text)
    sex = Column(String(10))
    issuing_country = Column(String(100))
    
    # Validation Results
    validation_overall = Column(Boolean, index=True)
    validation_details = Column(Text)  # JSON string
    face_match = Column(Boolean)
    face_match_distance = Column(Float)
    ocr_comparison_result = Column(Boolean)
    ocr_match_percentage = Column(Float)
    
    # Gemini API Results
    gemini_card_type = Column(String(50))
    gemini_confidence = Column(Float)
    gemini_extracted_fields = Column(Text)  # JSON string
    
    # File References
    portrait_file_path = Column(String(500))
    id_card_file_path = Column(String(500))
    
    # Audit Trail
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    validated_by = Column(String(50))
    validated_at = Column(DateTime)
    
    # Data Retention
    should_delete_after = Column(DateTime, index=True)
    is_deleted = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="submissions")
    validation_logs = relationship("ValidationLog", back_populates="submission")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_user_created', 'user_id', 'created_at'),
        Index('idx_validation_status', 'validation_overall', 'created_at'),
        Index('idx_id_type_created', 'id_type', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Submission(id={self.id}, submission_id={self.submission_id}, valid={self.validation_overall})>"
    
    def set_deletion_date(self, days: int = 90):
        """Set automatic deletion date"""
        self.should_delete_after = datetime.utcnow() + timedelta(days=days)


class ValidationLog(Base):
    """Detailed validation logs for each field"""
    __tablename__ = 'validation_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(String(50), unique=True, index=True, nullable=False)
    submission_id = Column(String(50), ForeignKey('submissions.submission_id'), index=True)
    
    # Validation Details
    field_name = Column(String(100), index=True)
    validation_type = Column(String(50))  # format, ocr_match, face_match
    validation_result = Column(Boolean)
    expected_value = Column(Text)
    actual_value = Column(Text)
    error_message = Column(Text)
    
    # Metadata
    validated_at = Column(DateTime, default=datetime.utcnow, index=True)
    validation_duration_ms = Column(Integer)
    
    # Relationships
    submission = relationship("Submission", back_populates="validation_logs")
    
    def __repr__(self):
        return f"<ValidationLog(field={self.field_name}, result={self.validation_result})>"


class APIUsage(Base):
    """Track Gemini API usage and costs"""
    __tablename__ = 'api_usage'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    usage_id = Column(String(50), unique=True, index=True, nullable=False)
    user_id = Column(String(50), ForeignKey('users.user_id'), index=True)
    submission_id = Column(String(50), ForeignKey('submissions.submission_id'))
    
    # API Call Details
    api_operation = Column(String(100))  # detect_card_type, extract_text, analyze_card
    model_name = Column(String(100))
    
    # Token Usage
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    total_tokens = Column(Integer)
    
    # Cost Tracking
    estimated_cost_usd = Column(Float)
    
    # Performance
    request_duration_ms = Column(Integer)
    success = Column(Boolean, index=True)
    error_message = Column(Text)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="api_usage")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_date', 'user_id', 'created_at'),
        Index('idx_operation_date', 'api_operation', 'created_at'),
    )
    
    def __repr__(self):
        return f"<APIUsage(operation={self.api_operation}, tokens={self.total_tokens}, cost=${self.estimated_cost_usd})>"


class AuditLog(Base):
    """System-wide audit logs"""
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(String(50), unique=True, index=True, nullable=False)
    
    # Event Information
    event_type = Column(String(100), index=True)
    event_category = Column(String(50), index=True)  # auth, validation, api, system
    event_description = Column(Text)
    
    # User Context
    user_id = Column(String(50), index=True)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Event Data
    event_data = Column(Text)  # JSON string
    severity = Column(String(20), index=True)  # info, warning, error, critical
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_event_date', 'event_type', 'created_at'),
        Index('idx_user_event', 'user_id', 'event_type', 'created_at'),
    )
    
    def __repr__(self):
        return f"<AuditLog(type={self.event_type}, severity={self.severity})>"
