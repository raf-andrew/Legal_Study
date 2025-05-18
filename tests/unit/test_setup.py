import pytest
import os
import sys

def test_python_version():
    """Test that we're using Python 3.x"""
    assert sys.version_info[0] == 3

def test_pytest_working():
    """Basic test to verify pytest is working"""
    assert True

def test_env_configuration():
    """Test that our environment configuration is accessible"""
    assert os.getenv('APP_NAME') == 'LegalStudy'

@pytest.mark.unit
def test_unit_marker():
    """Test that unit test marker is working"""
    assert True

@pytest.mark.integration
def test_integration_marker():
    """Test that integration test marker is working"""
    assert True

@pytest.mark.security
def test_security_marker():
    """Test that security test marker is working"""
    assert True

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
