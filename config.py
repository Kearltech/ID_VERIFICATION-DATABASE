"""
Centralized configuration management for ID Verification system.
Loads settings from environment variables with validation.
"""

import os
from dotenv import load_dotenv
from logger_config import audit_logger
from security import ConfigurationValidator, SecretsManager

# Load environment variables from .env file
load_dotenv()

# Configuration settings
class Config:
    """Application configuration settings."""
    
    # Environment
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development').lower()
    DEBUG = ENVIRONMENT == 'development'
    
    # API Configuration
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    API_TIMEOUT = int(os.getenv('API_TIMEOUT', '30'))
    API_MAX_RETRIES = int(os.getenv('API_MAX_RETRIES', '3'))
    API_RETRY_DELAY = int(os.getenv('API_RETRY_DELAY', '1'))
    
    # Rate Limiting
    RATE_LIMIT_CALLS_PER_MINUTE = int(os.getenv('RATE_LIMIT_CALLS_PER_MINUTE', '60'))
    MONTHLY_API_BUDGET_USD = float(os.getenv('MONTHLY_API_BUDGET_USD', '20.0'))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    LOG_FILE = os.getenv('LOG_FILE', 'logs/id_verification.log')
    LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', '10485760'))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))
    
    # File paths
    SUBMISSIONS_CSV = os.getenv('SUBMISSIONS_CSV', 'submissions.csv')
    UPLOADS_DIR = os.getenv('UPLOADS_DIR', 'uploads/')
    
    # Feature flags
    ENABLE_FACE_MATCHING = os.getenv('ENABLE_FACE_MATCHING', 'true').lower() == 'true'
    ENABLE_OCR = os.getenv('ENABLE_OCR', 'true').lower() == 'true'
    ENABLE_GEMINI_DETECTION = os.getenv('ENABLE_GEMINI_DETECTION', 'true').lower() == 'true'
    
    # Validation
    VALIDATE_ON_STARTUP = True
    
    @classmethod
    def validate_config(cls):
        """Validate configuration settings. Raises exception if validation fails."""
        validator = ConfigurationValidator()
        
        # Required configuration
        errors = []
        
        if not cls.GEMINI_API_KEY and cls.ENABLE_GEMINI_DETECTION:
            errors.append('GEMINI_API_KEY is required when ENABLE_GEMINI_DETECTION is true')
        
        if cls.MONTHLY_API_BUDGET_USD <= 0:
            errors.append('MONTHLY_API_BUDGET_USD must be positive')
        
        if cls.RATE_LIMIT_CALLS_PER_MINUTE <= 0:
            errors.append('RATE_LIMIT_CALLS_PER_MINUTE must be positive')
        
        if cls.API_MAX_RETRIES < 0:
            errors.append('API_MAX_RETRIES cannot be negative')
        
        if errors:
            audit_logger.error('Configuration validation failed', extra={
                'event': 'config_validation_failed',
                'errors': errors
            })
            raise ValueError(f"Configuration errors:\n" + "\n".join(errors))
        
        audit_logger.info('Configuration validated successfully', extra={
            'event': 'config_validated',
            'environment': cls.ENVIRONMENT,
            'features': {
                'face_matching': cls.ENABLE_FACE_MATCHING,
                'ocr': cls.ENABLE_OCR,
                'gemini_detection': cls.ENABLE_GEMINI_DETECTION
            }
        })
        
        return True
    
    @classmethod
    def to_dict(cls):
        """Return configuration as dictionary (excluding secrets)."""
        return {
            'environment': cls.ENVIRONMENT,
            'debug': cls.DEBUG,
            'api_timeout': cls.API_TIMEOUT,
            'api_max_retries': cls.API_MAX_RETRIES,
            'rate_limit_calls_per_minute': cls.RATE_LIMIT_CALLS_PER_MINUTE,
            'monthly_api_budget_usd': cls.MONTHLY_API_BUDGET_USD,
            'log_level': cls.LOG_LEVEL,
            'enable_face_matching': cls.ENABLE_FACE_MATCHING,
            'enable_ocr': cls.ENABLE_OCR,
            'enable_gemini_detection': cls.ENABLE_GEMINI_DETECTION,
        }


def get_config():
    """Get validated configuration."""
    if Config.VALIDATE_ON_STARTUP:
        Config.validate_config()
    return Config


# Validate configuration on module load if in production
if os.getenv('ENVIRONMENT', 'development').lower() == 'production':
    try:
        Config.validate_config()
    except ValueError as e:
        audit_logger.critical(f'Configuration validation failed on startup: {str(e)}', extra={'event': 'startup_config_failed'})
        raise
