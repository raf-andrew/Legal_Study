"""
Security configuration for chaos testing framework.
"""
import os
from pathlib import Path
from typing import Dict, List, Set

class SecurityConfig:
    def __init__(self):
        # Directory access control
        self.allowed_directories: Set[str] = {
            '.tests',
            '.errors',
            '.scripts',
            '.research',
            '.qa'
        }
        
        self.restricted_directories: Set[str] = {
            '.git',
            '.env',
            'venv',
            '__pycache__',
            'node_modules',
            '.config',
            '.ssh',
            '.aws'
        }
        
        # File type restrictions
        self.allowed_file_extensions: Set[str] = {
            '.md',
            '.py',
            '.txt',
            '.yaml',
            '.yml',
            '.json'
        }
        
        # Resource limits
        self.max_file_size_mb: int = 5  # Reduced from 10MB
        self.max_memory_usage_mb: int = 256  # Reduced from 512MB
        self.max_cpu_percent: float = 70.0  # Reduced from 80%
        self.max_disk_usage_percent: float = 85.0  # Reduced from 90%
        
        # Timeouts (reduced for faster failure detection)
        self.operation_timeout_seconds: int = 15  # Reduced from 30
        self.network_timeout_seconds: int = 5  # Reduced from 10
        self.recovery_timeout_seconds: int = 30  # Reduced from 60
        
        # Rate limiting (more restrictive)
        self.max_requests_per_minute: int = 30  # Reduced from 60
        self.max_file_operations_per_minute: int = 50  # Reduced from 100
        
        # Retry settings (more aggressive)
        self.max_retry_attempts: int = 2  # Reduced from 3
        self.retry_backoff_factor: float = 2.0  # Increased from 1.5
        
        # Logging settings
        self.log_level: str = "DEBUG"  # More verbose logging
        self.sensitive_fields: Set[str] = {
            "password",
            "token",
            "secret",
            "key",
            "auth",
            "credential",
            "api_key",
            "private_key",
            "certificate"
        }
        
        # Additional security measures
        self.max_concurrent_operations: int = 5
        self.max_file_depth: int = 3
        self.max_path_length: int = 100
        self.require_checksums: bool = True
        self.enforce_tls: bool = True
        self.require_authentication: bool = True
        
    def validate_path(self, path: str) -> bool:
        """Enhanced path validation with additional security checks."""
        path_obj = Path(path)
        
        # Check path length
        if len(str(path_obj)) > self.max_path_length:
            return False
            
        # Check path depth
        if len(path_obj.parts) > self.max_file_depth:
            return False
            
        # Check if path is absolute
        if path_obj.is_absolute():
            return False
            
        # Check for restricted directories
        parts = path_obj.parts
        if any(part in self.restricted_directories for part in parts):
            return False
            
        # Check for allowed directories
        if not any(str(path_obj).startswith(allowed) for allowed in self.allowed_directories):
            return False
            
        # Check file extension
        if path_obj.suffix and path_obj.suffix not in self.allowed_file_extensions:
            return False
            
        # Check for path traversal attempts
        if '..' in str(path_obj) or '//' in str(path_obj):
            return False
            
        return True
        
    def validate_file_size(self, file_path: str) -> bool:
        """Enhanced file size validation with additional checks."""
        try:
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if size_mb > self.max_file_size_mb:
                return False
                
            # Check file permissions
            if not os.access(file_path, os.R_OK):
                return False
                
            return True
        except OSError:
            return False
            
    def sanitize_log_message(self, message: str) -> str:
        """Enhanced log message sanitization."""
        message_str = str(message)
        
        # Remove sensitive fields
        for field in self.sensitive_fields:
            if field in message_str.lower():
                message_str = message_str.replace(field, "[REDACTED]")
                
        # Remove potential command injection
        message_str = message_str.replace(';', '[SEMICOLON]')
        message_str = message_str.replace('&&', '[AND]')
        message_str = message_str.replace('||', '[OR]')
        
        # Remove potential path traversal
        message_str = message_str.replace('..', '[DOTDOT]')
        message_str = message_str.replace('//', '[SLASHSLASH]')
        
        return message_str
        
    def get_security_headers(self) -> Dict[str, str]:
        """Enhanced security headers."""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';",
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
            'X-Permitted-Cross-Domain-Policies': 'none'
        }
        
    def validate_test_case(self, test_case: Dict) -> bool:
        """Enhanced test case validation."""
        content = str(test_case.get('content', ''))
        
        # Check for script injection
        if any(dangerous in content.lower() for dangerous in [
            '<script>', 'javascript:', 'eval(', 'exec(',
            'document.cookie', 'window.location', 'localStorage'
        ]):
            return False
            
        # Check for command injection
        if any(cmd in content.lower() for cmd in [
            'os.system', 'subprocess.', 'exec(', ';', '&&', '||',
            'eval(', 'compile(', 'execfile(', 'input(', 'raw_input('
        ]):
            return False
            
        # Check for file path traversal
        if '..' in content or '//' in content:
            return False
            
        # Check for sensitive data
        if any(sensitive in content.lower() for sensitive in self.sensitive_fields):
            return False
            
        return True
        
    def get_allowed_imports(self) -> Set[str]:
        """Enhanced allowed imports list."""
        return {
            'os.path',
            'pathlib',
            'typing',
            'datetime',
            'random',
            'time',
            'traceback',
            'sys',
            'enum',
            'dataclasses',
            'collections',
            'logging',
            'json',
            'yaml',
            're'
        }
        
    def validate_import(self, module: str) -> bool:
        """Enhanced import validation."""
        allowed = self.get_allowed_imports()
        return any(module.startswith(allowed) for allowed in allowed)
        
    def validate_resource_usage(self) -> bool:
        """Validate current resource usage against limits."""
        try:
            import psutil
            process = psutil.Process()
            
            # Check memory usage
            memory_percent = process.memory_percent()
            if memory_percent > self.max_memory_usage_mb:
                return False
                
            # Check CPU usage
            cpu_percent = process.cpu_percent(interval=1)
            if cpu_percent > self.max_cpu_percent:
                return False
                
            # Check disk usage
            disk_usage = psutil.disk_usage('/').percent
            if disk_usage > self.max_disk_usage_percent:
                return False
                
            return True
        except Exception:
            return False 