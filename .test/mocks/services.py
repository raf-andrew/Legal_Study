from typing import Dict, List, Optional
from unittest.mock import MagicMock

class MockService:
    """Base class for mock services."""
    def __init__(self, name: str, status: str = "healthy"):
        self.name = name
        self.status = status
        self.calls = []

    def record_call(self, method: str, *args, **kwargs):
        """Record method calls for testing."""
        self.calls.append({
            'method': method,
            'args': args,
            'kwargs': kwargs
        })

class MockConfigService(MockService):
    """Mock service for configuration management."""
    def __init__(self):
        super().__init__("config")
        self.configs: Dict[str, Dict] = {}

    def load_config(self, path: str) -> Dict:
        """Mock loading configuration."""
        self.record_call('load_config', path)
        return self.configs.get(path, {})

    def save_config(self, path: str, config: Dict):
        """Mock saving configuration."""
        self.record_call('save_config', path, config)
        self.configs[path] = config

class MockDirectoryService(MockService):
    """Mock service for directory operations."""
    def __init__(self):
        super().__init__("directory")
        self.directories: List[str] = []

    def check_directory(self, path: str) -> bool:
        """Mock directory check."""
        self.record_call('check_directory', path)
        return path in self.directories

    def create_directory(self, path: str):
        """Mock directory creation."""
        self.record_call('create_directory', path)
        self.directories.append(path)

class MockSecurityService(MockService):
    """Mock service for security operations."""
    def __init__(self):
        super().__init__("security")
        self.tokens: Dict[str, str] = {}
        self.permissions: Dict[str, List[str]] = {}

    def validate_token(self, token: str) -> bool:
        """Mock token validation."""
        self.record_call('validate_token', token)
        return token in self.tokens

    def check_permission(self, token: str, permission: str) -> bool:
        """Mock permission check."""
        self.record_call('check_permission', token, permission)
        return permission in self.permissions.get(token, [])

class MockMonitoringService(MockService):
    """Mock service for monitoring operations."""
    def __init__(self):
        super().__init__("monitoring")
        self.metrics: Dict[str, float] = {}
        self.alerts: List[Dict] = []

    def record_metric(self, name: str, value: float):
        """Mock metric recording."""
        self.record_call('record_metric', name, value)
        self.metrics[name] = value

    def create_alert(self, name: str, condition: str, threshold: float):
        """Mock alert creation."""
        self.record_call('create_alert', name, condition, threshold)
        self.alerts.append({
            'name': name,
            'condition': condition,
            'threshold': threshold
        })

class MockLoggingService(MockService):
    """Mock service for logging operations."""
    def __init__(self):
        super().__init__("logging")
        self.logs: List[Dict] = []

    def log(self, level: str, message: str, **kwargs):
        """Mock log entry."""
        self.record_call('log', level, message, **kwargs)
        self.logs.append({
            'level': level,
            'message': message,
            'metadata': kwargs
        })

class ServiceMockFactory:
    """Factory for creating mock services."""
    @staticmethod
    def create_mock_services() -> Dict[str, MockService]:
        """Create all mock services."""
        return {
            'config': MockConfigService(),
            'directory': MockDirectoryService(),
            'security': MockSecurityService(),
            'monitoring': MockMonitoringService(),
            'logging': MockLoggingService()
        }

    @staticmethod
    def get_mock_service(name: str) -> Optional[MockService]:
        """Get a specific mock service."""
        services = ServiceMockFactory.create_mock_services()
        return services.get(name) 