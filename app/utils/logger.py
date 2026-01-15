import logging
import logging.handlers
import os
from datetime import datetime
from app.database import get_settings
import json

# Create logs directory if it doesn't exist
LOGS_DIR = "/app/logs" if os.path.exists("/app") else "logs"
os.makedirs(LOGS_DIR, exist_ok=True)

class SanitizedFormatter(logging.Formatter):
    """Custom formatter that sanitizes sensitive information"""
    
    SENSITIVE_KEYS = {'password', 'pwd', 'secret', 'token', 'authorization', 'api_key', 'credit_card'}
    
    def format(self, record):
        # Create a copy of the record
        if isinstance(record.msg, dict):
            # If message is a dict, sanitize it
            sanitized = self._sanitize_dict(record.msg.copy())
            record.msg = sanitized
        
        # Format the message
        result = super().format(record)
        return result
    
    def _sanitize_dict(self, data: dict) -> dict:
        """Recursively sanitize dictionary"""
        for key in data:
            if any(sensitive in key.lower() for sensitive in self.SENSITIVE_KEYS):
                data[key] = "***REDACTED***"
            elif isinstance(data[key], dict):
                data[key] = self._sanitize_dict(data[key])
        return data

def setup_logging():
    """Setup application logging"""
    settings = get_settings()
    log_level = settings.log_level
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(LOGS_DIR, "app.log"),
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(log_level)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # Formatter
    formatter = SanitizedFormatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def log_user_action(action: str, user_id: int, details: dict = None, level: str = "INFO"):
    """Log user actions without sensitive data"""
    logger = logging.getLogger(__name__)
    
    log_data = {
        'action': action,
        'user_id': user_id,
        'timestamp': datetime.utcnow().isoformat(),
    }
    
    if details:
        # Remove sensitive fields
        sanitized_details = {k: v for k, v in details.items() 
                            if not any(s in k.lower() for s in ['password', 'token', 'secret'])}
        log_data['details'] = sanitized_details
    
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(f"User Action: {json.dumps(log_data)}")

def log_game_action(action: str, user_id: int, game_id: int, details: dict = None):
    """Log game-related actions"""
    logger = logging.getLogger(__name__)
    
    log_data = {
        'action': action,
        'user_id': user_id,
        'game_id': game_id,
        'timestamp': datetime.utcnow().isoformat(),
    }
    
    if details:
        log_data['details'] = details
    
    logger.info(f"Game Action: {json.dumps(log_data)}")

def log_error(error_msg: str, error_type: str, user_id: int = None, context: dict = None):
    """Log error with context"""
    logger = logging.getLogger(__name__)
    
    log_data = {
        'error': error_msg,
        'error_type': error_type,
        'timestamp': datetime.utcnow().isoformat(),
    }
    
    if user_id:
        log_data['user_id'] = user_id
    if context:
        log_data['context'] = context
    
    logger.error(f"Error: {json.dumps(log_data)}")
