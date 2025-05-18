#!/usr/bin/env python3

import os
import sys
import pytest
import logging
from pathlib import Path
from fastapi.testclient import TestClient
from datetime import datetime

from app.main import app
from app.core.config import settings
from app.core.database import get_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.testing/smoke_test.log'),
        logging.StreamHandler()
    ]
)

class SmokeTest:
    def __init__(self):
        self.workspace_root = Path(os.getcwd())
        self.client = TestClient(app)
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'errors': []
        }
        
    def test_health_endpoint(self):
        """Test the health check endpoint"""
        try:
            response = self.client.get("/health")
            assert response.status_code == 200
            assert response.json()['status'] == 'healthy'
            
            self.results['tests']['health_endpoint'] = {
                'status': 'pass',
                'response_time': response.elapsed.total_seconds()
            }
            return True
        except Exception as e:
            self.results['tests']['health_endpoint'] = {
                'status': 'fail',
                'error': str(e)
            }
            self.results['errors'].append(f"Health endpoint test failed: {str(e)}")
            return False
            
    def test_version_endpoint(self):
        """Test the API version endpoint"""
        try:
            response = self.client.get("/api/v1/version")
            assert response.status_code == 200
            assert 'version' in response.json()
            
            self.results['tests']['version_endpoint'] = {
                'status': 'pass',
                'response_time': response.elapsed.total_seconds()
            }
            return True
        except Exception as e:
            self.results['tests']['version_endpoint'] = {
                'status': 'fail',
                'error': str(e)
            }
            self.results['errors'].append(f"Version endpoint test failed: {str(e)}")
            return False
            
    def test_error_endpoint(self):
        """Test the error handling endpoint"""
        try:
            response = self.client.get("/api/v1/error")
            assert response.status_code == 500
            assert 'detail' in response.json()
            
            self.results['tests']['error_endpoint'] = {
                'status': 'pass',
                'response_time': response.elapsed.total_seconds()
            }
            return True
        except Exception as e:
            self.results['tests']['error_endpoint'] = {
                'status': 'fail',
                'error': str(e)
            }
            self.results['errors'].append(f"Error endpoint test failed: {str(e)}")
            return False
            
    def test_protected_endpoint(self):
        """Test the protected endpoint"""
        try:
            # Test without token
            response = self.client.get("/api/v1/protected")
            assert response.status_code == 401
            
            # Test with invalid token
            response = self.client.get(
                "/api/v1/protected",
                headers={"Authorization": "Bearer invalid_token"}
            )
            assert response.status_code == 401
            
            self.results['tests']['protected_endpoint'] = {
                'status': 'pass',
                'response_time': response.elapsed.total_seconds()
            }
            return True
        except Exception as e:
            self.results['tests']['protected_endpoint'] = {
                'status': 'fail',
                'error': str(e)
            }
            self.results['errors'].append(f"Protected endpoint test failed: {str(e)}")
            return False
            
    def test_search_endpoint(self):
        """Test the search endpoint"""
        try:
            # Test with valid query
            response = self.client.post(
                "/api/v1/search",
                json={"query": "test"}
            )
            assert response.status_code == 200
            
            # Test with invalid query
            response = self.client.post(
                "/api/v1/search",
                json={}
            )
            assert response.status_code == 400
            
            self.results['tests']['search_endpoint'] = {
                'status': 'pass',
                'response_time': response.elapsed.total_seconds()
            }
            return True
        except Exception as e:
            self.results['tests']['search_endpoint'] = {
                'status': 'fail',
                'error': str(e)
            }
            self.results['errors'].append(f"Search endpoint test failed: {str(e)}")
            return False
            
    def test_comment_endpoint(self):
        """Test the comment endpoint"""
        try:
            # Test without authentication
            response = self.client.post(
                "/api/v1/comment",
                json={"content": "test comment"}
            )
            assert response.status_code == 401
            
            self.results['tests']['comment_endpoint'] = {
                'status': 'pass',
                'response_time': response.elapsed.total_seconds()
            }
            return True
        except Exception as e:
            self.results['tests']['comment_endpoint'] = {
                'status': 'fail',
                'error': str(e)
            }
            self.results['errors'].append(f"Comment endpoint test failed: {str(e)}")
            return False
            
    def save_results(self):
        """Save test results to file"""
        results_file = self.workspace_root / '.testing' / 'smoke_test_results.json'
        import json
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
            
    def run(self):
        """Run all smoke tests"""
        logging.info("Starting smoke tests...")
        
        success = True
        success &= self.test_health_endpoint()
        success &= self.test_version_endpoint()
        success &= self.test_error_endpoint()
        success &= self.test_protected_endpoint()
        success &= self.test_search_endpoint()
        success &= self.test_comment_endpoint()
        
        self.save_results()
        
        if success:
            logging.info("All smoke tests passed")
        else:
            logging.error("Some smoke tests failed")
            for error in self.results['errors']:
                logging.error(error)
                
        return success

@pytest.fixture(scope="module")
def test_client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)

@pytest.fixture(scope="module")
def test_db():
    """Create and configure test database."""
    from app.core.database import Base, engine
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Get database session
    db = next(get_db())
    
    yield db
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)
    db.close()

@pytest.fixture(scope="module")
def test_user(test_db):
    """Create a test user for authentication tests."""
    from app.models import User
    from app.core.security import get_password_hash
    
    user = User(
        username="test_user",
        email="test@example.com",
        password_hash=get_password_hash("test_password"),
        is_active=True
    )
    
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    
    yield user
    
    test_db.delete(user)
    test_db.commit()

if __name__ == '__main__':
    test = SmokeTest()
    success = test.run()
    sys.exit(0 if success else 1) 