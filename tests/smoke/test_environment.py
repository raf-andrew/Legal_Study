import pytest
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.logs/smoke/environment.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def setup_module(module):
    """Setup for this test module."""
    logger.info(f"Starting environment smoke tests at {datetime.now()}")
    load_dotenv('.env.dev')

def teardown_module(module):
    """Teardown for this test module."""
    logger.info(f"Completed environment smoke tests at {datetime.now()}")

@pytest.mark.smoke
def test_required_env_vars():
    """Test that all required environment variables are set."""
    required_vars = [
        'APP_NAME',
        'DEBUG',
        'TESTING',
        'API_VERSION',
        'DATABASE_URL',
        'SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
            logger.error(f"Missing required environment variable: {var}")
    
    if missing_vars:
        with open('.errors/environment_errors.log', 'a') as f:
            f.write(f"\n{datetime.now()} - Missing environment variables: {', '.join(missing_vars)}")
    
    assert not missing_vars, f"Missing required environment variables: {', '.join(missing_vars)}"

@pytest.mark.smoke
def test_database_url_format():
    """Test that the database URL is properly formatted."""
    db_url = os.getenv('DATABASE_URL')
    assert db_url.startswith(('sqlite:///', 'postgresql://', 'mysql://')), \
        f"Invalid database URL format: {db_url}"

@pytest.mark.smoke
def test_api_version_format():
    """Test that the API version is properly formatted."""
    api_version = os.getenv('API_VERSION')
    assert api_version.startswith('v'), \
        f"API version should start with 'v', got: {api_version}"

@pytest.mark.smoke
def test_security_settings():
    """Test that security-related settings are properly configured."""
    assert os.getenv('SECRET_KEY'), "SECRET_KEY must be set"
    assert os.getenv('ALGORITHM') == 'HS256', "ALGORITHM must be HS256"
    assert int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', 0)) > 0, \
        "ACCESS_TOKEN_EXPIRE_MINUTES must be positive"

@pytest.mark.smoke
def test_cors_settings():
    """Test that CORS settings are properly configured."""
    cors_origins = os.getenv('CORS_ORIGINS')
    assert cors_origins, "CORS_ORIGINS must be set"
    # For development, we expect ["*"]
    assert cors_origins == '["*"]', "CORS_ORIGINS should be ['*'] in development"

if __name__ == '__main__':
    pytest.main([__file__, '-v']) 