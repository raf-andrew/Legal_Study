import os
import sys
import shutil
from pathlib import Path

def setup_environment():
    # Create necessary directories
    directories = [
        '.codespaces/logs',
        '.codespaces/complete',
        '.codespaces/verification',
        '.codespaces/services',
        '.codespaces/config'
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

    # Create .env file from example if it doesn't exist
    env_example = Path('.env.example')
    env_file = Path('.env')

    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print("Created .env file from .env.example")

    # Create Codespaces-specific config
    codespaces_config = {
        'APP_NAME': 'LegalStudy',
        'APP_ENV': 'local',
        'APP_DEBUG': 'true',
        'APP_URL': 'http://localhost:8000',
        'CODESPACES': 'true',
        'CODESPACES_DB_HOST': os.getenv('CODESPACE_DB_HOST', 'localhost'),
        'CODESPACES_DB_PORT': os.getenv('CODESPACE_DB_PORT', '3306'),
        'CODESPACES_REDIS_HOST': os.getenv('CODESPACE_REDIS_HOST', 'localhost'),
        'CODESPACES_REDIS_PORT': os.getenv('CODESPACE_REDIS_PORT', '6379'),
        'DB_CONNECTION': 'mysql',
        'DB_HOST': os.getenv('CODESPACE_DB_HOST', 'localhost'),
        'DB_PORT': os.getenv('CODESPACE_DB_PORT', '3306'),
        'DB_DATABASE': 'legal_study',
        'DB_USERNAME': 'root',
        'DB_PASSWORD': '',
        'REDIS_HOST': os.getenv('CODESPACE_REDIS_HOST', 'localhost'),
        'REDIS_PASSWORD': 'null',
        'REDIS_PORT': os.getenv('CODESPACE_REDIS_PORT', '6379'),
        'CACHE_DRIVER': 'redis',
        'QUEUE_CONNECTION': 'redis',
        'SESSION_DRIVER': 'redis',
        'SERVICES_ENABLED': 'true',
        'SERVICES_CONFIG_PATH': '.codespaces/services',
        'SERVICES_LOG_PATH': '.codespaces/logs',
        'SERVICES_COMPLETE_PATH': '.codespaces/complete',
        'SERVICES_VERIFICATION_PATH': '.codespaces/verification'
    }

    # Write Codespaces config
    config_file = Path('.codespaces/config/codespaces.env')
    with open(config_file, 'w') as f:
        for key, value in codespaces_config.items():
            f.write(f"{key}={value}\n")

    print("Created Codespaces configuration file")

    # Create service configuration files
    services = {
        'database': {
            'type': 'mysql',
            'host': os.getenv('CODESPACE_DB_HOST', 'localhost'),
            'port': os.getenv('CODESPACE_DB_PORT', '3306'),
            'database': 'legal_study',
            'username': 'root',
            'password': ''
        },
        'redis': {
            'type': 'redis',
            'host': os.getenv('CODESPACE_REDIS_HOST', 'localhost'),
            'port': os.getenv('CODESPACE_REDIS_PORT', '6379'),
            'password': None
        }
    }

    for service, config in services.items():
        service_file = Path(f'.codespaces/services/{service}.json')
        with open(service_file, 'w') as f:
            import json
            json.dump(config, f, indent=2)

    print("Created service configuration files")

if __name__ == '__main__':
    setup_environment()
