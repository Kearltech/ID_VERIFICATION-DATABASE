"""
Centralized logging configuration for the ID Verification system.
Handles structured logging with file and console output.
"""

import logging
import logging.handlers
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for better parsing and analysis."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Convert log record to JSON."""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
        
        return json.dumps(log_data, default=str)


class AuditLogger:
    """Specialized logger for audit trail."""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger('audit')
        self.logger.setLevel(logging.INFO)
        
        # File handler for audit logs
        audit_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "audit.log",
            maxBytes=10_000_000,  # 10MB
            backupCount=5
        )
        audit_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(audit_handler)
    
    def log_submission(self, user_id: str, submission_data: Dict[str, Any], result: Dict[str, Any]):
        """Log a submission event."""
        self.logger.info(
            "Submission processed",
            extra={
                'user_id': user_id,
                'id_type': submission_data.get('id_type'),
                'validation_result': result.get('overall'),
                'face_match': result.get('face_match'),
                'submission_id': submission_data.get('id_number', 'UNKNOWN')
            }
        )
    
    def log_api_call(self, api_name: str, status: str, duration: float, tokens: Dict[str, int] = None):
        """Log API call metrics."""
        self.logger.info(
            f"API call: {api_name}",
            extra={
                'api_name': api_name,
                'status': status,
                'duration_seconds': duration,
                'tokens_in': tokens.get('input', 0) if tokens else 0,
                'tokens_out': tokens.get('output', 0) if tokens else 0
            }
        )
    
    def log_validation_failure(self, user_id: str, error_code: str, details: Dict[str, Any]):
        """Log validation failures."""
        self.logger.warning(
            f"Validation failed: {error_code}",
            extra={
                'user_id': user_id,
                'error_code': error_code,
                **details
            }
        )


def setup_logging(
    app_name: str = "id_verification",
    log_level: str = "INFO",
    log_dir: str = "logs",
    enable_file_handler: bool = True,
    enable_console_handler: bool = True
) -> logging.Logger:
    """
    Setup centralized logging for the application.
    
    Args:
        app_name: Name of the application
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
        enable_file_handler: Whether to write logs to file
        enable_console_handler: Whether to print logs to console
    
    Returns:
        Configured logger instance
    """
    # Create logs directory
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(app_name)
    logger.setLevel(getattr(logging, log_level))
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Console handler (human-readable)
    if enable_console_handler:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level))
        
        # Simple format for console
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # File handler (JSON format for parsing)
    if enable_file_handler:
        file_handler = logging.handlers.RotatingFileHandler(
            log_path / f"{app_name}.log",
            maxBytes=10_000_000,  # 10MB per file
            backupCount=5  # Keep 5 backup files
        )
        file_handler.setLevel(getattr(logging, log_level))
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)
        
        # Error-only file handler
        error_handler = logging.handlers.RotatingFileHandler(
            log_path / f"{app_name}_errors.log",
            maxBytes=10_000_000,
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(JSONFormatter())
        logger.addHandler(error_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance by name.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Module-level logger for this package
logger = setup_logging()
audit_logger = AuditLogger()


if __name__ == "__main__":
    # Test logging
    test_logger = setup_logging(log_level="DEBUG")
    
    test_logger.debug("This is a debug message")
    test_logger.info("This is an info message")
    test_logger.warning("This is a warning message")
    test_logger.error("This is an error message")
    
    # Test audit logger
    audit_logger.log_submission(
        user_id="user_123",
        submission_data={
            'id_type': 'Ghana Card',
            'id_number': 'GHA-123456789-0'
        },
        result={
            'overall': True,
            'face_match': True
        }
    )
    
    print("\n✓ Logging configured successfully!")
    print(f"  - Check logs/ directory for log files")
