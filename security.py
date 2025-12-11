"""
Security and secrets management for the ID Verification system.
Handles API keys and sensitive configuration securely.
"""

import os
import logging
from typing import Optional, Dict, Any, Tuple
from dotenv import load_dotenv
from exceptions import ConfigurationError, SecurityError, create_error

logger = logging.getLogger(__name__)


class SecretsManager:
    """Manage sensitive configuration and API keys."""
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize secrets manager.
        
        Args:
            env_file: Path to .env file (optional)
        """
        # Load .env file if provided
        if env_file and os.path.exists(env_file):
            load_dotenv(env_file)
            logger.info(f"Loaded environment from {env_file}")
        elif env_file:
            logger.warning(f"Environment file not found: {env_file}")
    
    @staticmethod
    def get_api_key(key_name: str, required: bool = True) -> Optional[str]:
        """
        Get API key from environment.
        
        Args:
            key_name: Environment variable name
            required: Whether key is required
        
        Returns:
            API key value
        
        Raises:
            ConfigurationError: If required key is missing
        """
        value = os.getenv(key_name)
        
        if not value:
            if required:
                error = create_error(
                    'CONFIG_MISSING',
                    f"Required environment variable not set: {key_name}",
                    {'env_var': key_name},
                    ConfigurationError
                )
                logger.error(error.message)
                raise error
            return None
        
        # Validate key format (basic checks)
        if len(value) < 10:
            logger.warning(f"API key {key_name} seems too short (length: {len(value)})")
        
        return value
    
    @staticmethod
    def get_gemini_api_key() -> str:
        """
        Get Gemini API key from environment.
        
        Returns:
            Gemini API key
        
        Raises:
            ConfigurationError: If key not found
        """
        try:
            key = SecretsManager.get_api_key('GEMINI_API_KEY', required=True)
            
            if not key.startswith('AI'):
                logger.warning("Gemini API key does not start with 'AI' (unexpected format)")
            
            return key
        except ConfigurationError:
            raise
    
    @staticmethod
    def validate_api_key(api_key: str, key_type: str = 'GEMINI') -> bool:
        """
        Validate API key format.
        
        Args:
            api_key: API key to validate
            key_type: Type of API key
        
        Returns:
            True if key is valid format
        """
        if not api_key or not isinstance(api_key, str):
            return False
        
        if len(api_key) < 20:
            return False
        
        if key_type == 'GEMINI' and not api_key.startswith('AI'):
            return False
        
        return True
    
    @staticmethod
    def get_config_value(
        key: str,
        default: Any = None,
        type_cast: type = str
    ) -> Any:
        """
        Get configuration value from environment.
        
        Args:
            key: Environment variable name
            default: Default value if not found
            type_cast: Type to cast value to
        
        Returns:
            Configuration value
        """
        value = os.getenv(key, default)
        
        if value is not None and type_cast != str:
            try:
                value = type_cast(value)
            except (ValueError, TypeError) as e:
                logger.warning(f"Could not cast {key} to {type_cast}: {e}")
                return default
        
        return value


class SecurityValidator:
    """Validate security-related configurations."""
    
    @staticmethod
    def validate_api_key_provided(api_key: Optional[str]) -> bool:
        """
        Validate that API key is provided.
        
        Args:
            api_key: API key to validate
        
        Returns:
            True if valid
        
        Raises:
            SecurityError: If validation fails
        """
        if not api_key:
            error = create_error(
                'API_KEY_INVALID',
                'API key is missing',
                {},
                SecurityError
            )
            logger.error(error.message)
            raise error
        
        if not SecretsManager.validate_api_key(api_key):
            error = create_error(
                'API_KEY_INVALID',
                f'Invalid API key format (length: {len(api_key)})',
                {'key_length': len(api_key)},
                SecurityError
            )
            logger.error(error.message)
            raise error
        
        return True
    
    @staticmethod
    def check_sensitive_data_in_logs(data: str, sensitive_fields: list = None) -> bool:
        """
        Check if sensitive data appears to be in logs.
        
        Args:
            data: Data to check
            sensitive_fields: List of sensitive field names to look for
        
        Returns:
            True if no sensitive data detected
        """
        if not sensitive_fields:
            sensitive_fields = ['api_key', 'password', 'token', 'secret']
        
        data_lower = data.lower()
        
        for field in sensitive_fields:
            if field in data_lower:
                logger.warning(f"Potential sensitive data detected: {field}")
                return False
        
        return True


class ConfigurationValidator:
    """Validate system configuration."""
    
    REQUIRED_CONFIGS = {
        'GEMINI_API_KEY': str,
        'ENVIRONMENT': str,
    }
    
    OPTIONAL_CONFIGS = {
        'LOG_LEVEL': str,
        'ENCRYPTION_MASTER_KEY': str,
        'MAX_IMAGE_SIZE_MB': int,
        'FACE_MATCH_TOLERANCE': float,
    }
    
    DEFAULT_VALUES = {
        'ENVIRONMENT': 'development',
        'LOG_LEVEL': 'INFO',
        'MAX_IMAGE_SIZE_MB': 10,
        'FACE_MATCH_TOLERANCE': 0.6,
    }
    
    @classmethod
    def validate_all(cls) -> Tuple[bool, Dict[str, str]]:
        """
        Validate all required configurations.
        
        Returns:
            Tuple of (is_valid, errors_dict)
        """
        errors = {}
        
        # Check required configs
        for config_key, expected_type in cls.REQUIRED_CONFIGS.items():
            value = os.getenv(config_key)
            
            if not value:
                errors[config_key] = f"Required configuration missing"
                continue
            
            try:
                if expected_type == int:
                    int(value)
                elif expected_type == float:
                    float(value)
            except ValueError:
                errors[config_key] = f"Invalid type, expected {expected_type.__name__}"
        
        # Validate optional configs if provided
        for config_key, expected_type in cls.OPTIONAL_CONFIGS.items():
            value = os.getenv(config_key)
            
            if value:
                try:
                    if expected_type == int:
                        int(value)
                    elif expected_type == float:
                        float(value)
                except ValueError:
                    errors[config_key] = f"Invalid type, expected {expected_type.__name__}"
        
        return len(errors) == 0, errors
    
    @classmethod
    def get_validated_config(cls) -> Dict[str, Any]:
        """
        Get validated configuration dictionary.
        
        Returns:
            Configuration dictionary
        
        Raises:
            ConfigurationError: If validation fails
        """
        is_valid, errors = cls.validate_all()
        
        if not is_valid:
            error_msg = "; ".join([f"{k}: {v}" for k, v in errors.items()])
            raise create_error(
                'CONFIG_INVALID',
                f"Configuration validation failed: {error_msg}",
                {'errors': errors},
                ConfigurationError
            )
        
        config = {}
        
        # Add required configs
        for config_key in cls.REQUIRED_CONFIGS.keys():
            config[config_key] = os.getenv(config_key)
        
        # Add optional configs with defaults
        for config_key, type_cast in cls.OPTIONAL_CONFIGS.items():
            default = cls.DEFAULT_VALUES.get(config_key)
            config[config_key] = SecretsManager.get_config_value(
                config_key,
                default=default,
                type_cast=type_cast
            )
        
        logger.info("Configuration validated successfully")
        return config


if __name__ == "__main__":
    print("Security and Configuration Testing...\n")
    
    # Create test .env file
    test_env = """
GEMINI_API_KEY=AIzaSyExample123456789
ENVIRONMENT=development
LOG_LEVEL=DEBUG
MAX_IMAGE_SIZE_MB=10
FACE_MATCH_TOLERANCE=0.6
"""
    
    with open(".env.test", "w") as f:
        f.write(test_env)
    
    # Test SecretsManager
    print("Testing SecretsManager:")
    secrets = SecretsManager(".env.test")
    
    try:
        key = SecretsManager.get_api_key("GEMINI_API_KEY")
        print(f"  ✓ Got API key (length: {len(key)})")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    print("\nTesting SecurityValidator:")
    try:
        SecurityValidator.validate_api_key_provided("AIzaSyExample123456789")
        print("  ✓ Valid API key")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    print("\nTesting ConfigurationValidator:")
    try:
        config = ConfigurationValidator.get_validated_config()
        print(f"  ✓ Config validated (keys: {list(config.keys())})")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # Cleanup
    import os as os_module
    if os_module.path.exists(".env.test"):
        os_module.remove(".env.test")
