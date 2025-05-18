# Testing Guide

This guide explains the testing system in the Legal Study Platform.

## Overview

The platform implements a comprehensive testing system with support for:

- Unit testing
- Integration testing
- Functional testing
- Performance testing
- Security testing

## Test Directory Structure

```
tests/
├── unit/
│   ├── models/
│   ├── services/
│   └── utils/
├── integration/
│   ├── api/
│   └── database/
├── functional/
│   ├── api/
│   └── ui/
├── performance/
│   ├── load/
│   └── stress/
└── security/
    ├── auth/
    └── api/
```

## Test Configuration

### 1. Test Setup

```python
# tests/conftest.py
import pytest
from app import create_app
from app.extensions import db
from app.models import User, Document

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def db_session(app):
    connection = db.engine.connect()
    transaction = connection.begin()
    session = db.create_scoped_session(
        options=dict(bind=connection, binds={})
    )
    db.session = session
    yield session
    transaction.rollback()
    connection.close()
    session.remove()
```

## Unit Testing

### 1. Model Tests

```python
# tests/unit/models/test_user.py
import pytest
from app.models import User

def test_create_user(db_session):
    user = User(
        email='test@example.com',
        name='Test User'
    )
    user.set_password('password123')
    db_session.add(user)
    db_session.commit()

    assert user.id is not None
    assert user.email == 'test@example.com'
    assert user.name == 'Test User'
    assert user.verify_password('password123')

def test_user_validation(db_session):
    with pytest.raises(ValueError):
        User(
            email='invalid-email',
            name='Test User'
        )

def test_password_validation():
    user = User(email='test@example.com', name='Test User')
    with pytest.raises(ValueError):
        user.set_password('short')
```

### 2. Service Tests

```python
# tests/unit/services/test_auth.py
import pytest
from app.services import AuthService
from app.models import User

def test_create_token(db_session):
    user = User(email='test@example.com', name='Test User')
    user.set_password('password123')
    db_session.add(user)
    db_session.commit()

    token = AuthService.create_token(user.id)
    assert token is not None

    payload = AuthService.verify_token(token)
    assert payload['user_id'] == user.id

def test_verify_invalid_token():
    with pytest.raises(ValueError):
        AuthService.verify_token('invalid-token')

def test_authenticate_user(db_session):
    user = User(email='test@example.com', name='Test User')
    user.set_password('password123')
    db_session.add(user)
    db_session.commit()

    authenticated_user = AuthService.authenticate(
        'test@example.com',
        'password123'
    )
    assert authenticated_user.id == user.id

    with pytest.raises(ValueError):
        AuthService.authenticate('test@example.com', 'wrong-password')
```

## Integration Testing

### 1. API Tests

```python
# tests/integration/api/test_auth.py
import pytest
from app.models import User

def test_register(client, db_session):
    response = client.post('/api/auth/register', json={
        'email': 'test@example.com',
        'name': 'Test User',
        'password': 'password123'
    })
    assert response.status_code == 201
    assert response.json['email'] == 'test@example.com'

    user = User.query.filter_by(email='test@example.com').first()
    assert user is not None
    assert user.name == 'Test User'

def test_login(client, db_session):
    # Create user
    user = User(email='test@example.com', name='Test User')
    user.set_password('password123')
    db_session.add(user)
    db_session.commit()

    # Test login
    response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    assert response.status_code == 200
    assert 'token' in response.json

def test_protected_route(client, db_session):
    # Create user and get token
    user = User(email='test@example.com', name='Test User')
    user.set_password('password123')
    db_session.add(user)
    db_session.commit()

    login_response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    token = login_response.json['token']

    # Test protected route
    response = client.get(
        '/api/documents',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
```

### 2. Database Tests

```python
# tests/integration/database/test_document.py
import pytest
from app.models import Document, Tag

def test_create_document(db_session):
    document = Document(
        title='Test Document',
        content='Test Content',
        type='legal'
    )
    db_session.add(document)
    db_session.commit()

    assert document.id is not None
    assert document.title == 'Test Document'
    assert document.content == 'Test Content'
    assert document.type == 'legal'

def test_document_tags(db_session):
    document = Document(
        title='Test Document',
        content='Test Content',
        type='legal'
    )
    tag1 = Tag(name='tag1')
    tag2 = Tag(name='tag2')
    document.tags = [tag1, tag2]
    db_session.add(document)
    db_session.commit()

    assert len(document.tags) == 2
    assert document.tags[0].name == 'tag1'
    assert document.tags[1].name == 'tag2'
```

## Functional Testing

### 1. API Workflow Tests

```python
# tests/functional/api/test_document_workflow.py
import pytest
from app.models import User, Document

def test_document_workflow(client, db_session):
    # Register user
    client.post('/api/auth/register', json={
        'email': 'test@example.com',
        'name': 'Test User',
        'password': 'password123'
    })

    # Login
    login_response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    token = login_response.json['token']

    # Create document
    create_response = client.post(
        '/api/documents',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'title': 'Test Document',
            'content': 'Test Content',
            'type': 'legal',
            'tags': ['tag1', 'tag2']
        }
    )
    assert create_response.status_code == 201
    document_id = create_response.json['id']

    # Get document
    get_response = client.get(
        f'/api/documents/{document_id}',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert get_response.status_code == 200
    assert get_response.json['title'] == 'Test Document'
    assert get_response.json['content'] == 'Test Content'
    assert len(get_response.json['tags']) == 2
```

### 2. UI Tests

```python
# tests/functional/ui/test_document_creation.py
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

@pytest.fixture
def driver():
    driver = webdriver.Chrome()
    yield driver
    driver.quit()

def test_create_document_ui(driver, app, db_session):
    # Create test user
    from app.models import User
    user = User(email='test@example.com', name='Test User')
    user.set_password('password123')
    db_session.add(user)
    db_session.commit()

    # Login
    driver.get('http://localhost:5000/login')
    driver.find_element(By.NAME, 'email').send_keys('test@example.com')
    driver.find_element(By.NAME, 'password').send_keys('password123')
    driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

    # Create document
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.LINK_TEXT, 'New Document'))
    ).click()

    driver.find_element(By.NAME, 'title').send_keys('Test Document')
    driver.find_element(By.NAME, 'content').send_keys('Test Content')
    driver.find_element(By.NAME, 'type').send_keys('legal')
    driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()

    # Verify document created
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'document-title'))
    )
    assert driver.find_element(By.CLASS_NAME, 'document-title').text == 'Test Document'
```

## Performance Testing

### 1. Load Testing

```python
# tests/performance/load/test_document_api.py
from locust import HttpUser, task, between

class DocumentUser(HttpUser):
    wait_time = between(1, 3)
    token = None

    def on_start(self):
        # Login
        response = self.client.post('/api/auth/login', json={
            'email': 'test@example.com',
            'password': 'password123'
        })
        self.token = response.json['token']

    @task
    def get_documents(self):
        self.client.get(
            '/api/documents',
            headers={'Authorization': f'Bearer {self.token}'}
        )

    @task
    def create_document(self):
        self.client.post(
            '/api/documents',
            headers={'Authorization': f'Bearer {self.token}'},
            json={
                'title': 'Test Document',
                'content': 'Test Content',
                'type': 'legal'
            }
        )
```

### 2. Stress Testing

```python
# tests/performance/stress/test_document_endpoint.py
import asyncio
import aiohttp
import pytest
from app.models import User

async def make_request(session, url, token):
    async with session.get(
        url,
        headers={'Authorization': f'Bearer {token}'}
    ) as response:
        return response.status

@pytest.mark.asyncio
async def test_document_endpoint_stress(app, db_session):
    # Create test user and get token
    user = User(email='test@example.com', name='Test User')
    user.set_password('password123')
    db_session.add(user)
    db_session.commit()

    async with aiohttp.ClientSession() as session:
        # Login
        async with session.post(
            'http://localhost:5000/api/auth/login',
            json={
                'email': 'test@example.com',
                'password': 'password123'
            }
        ) as response:
            token = (await response.json())['token']

        # Make concurrent requests
        tasks = []
        for _ in range(100):
            task = make_request(
                session,
                'http://localhost:5000/api/documents',
                token
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        success_count = results.count(200)
        assert success_count / len(results) > 0.95
```

## Security Testing

### 1. Authentication Tests

```python
# tests/security/auth/test_password.py
import pytest
from app.models import User

def test_password_hashing():
    user = User(email='test@example.com', name='Test User')
    user.set_password('password123')
    assert user.password_hash != 'password123'
    assert user.verify_password('password123')
    assert not user.verify_password('wrong-password')

def test_token_security(client, db_session):
    # Create user
    user = User(email='test@example.com', name='Test User')
    user.set_password('password123')
    db_session.add(user)
    db_session.commit()

    # Get token
    response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    token = response.json['token']

    # Test token expiration
    import time
    time.sleep(2)  # Wait for token to expire
    response = client.get(
        '/api/documents',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 401
```

### 2. API Security Tests

```python
# tests/security/api/test_security.py
import pytest
from app.models import User

def test_csrf_protection(client, db_session):
    # Create user and get token
    user = User(email='test@example.com', name='Test User')
    user.set_password('password123')
    db_session.add(user)
    db_session.commit()

    login_response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    token = login_response.json['token']

    # Test without CSRF token
    response = client.post(
        '/api/documents',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'title': 'Test Document',
            'content': 'Test Content'
        }
    )
    assert response.status_code == 403

def test_rate_limiting(client):
    for _ in range(100):
        response = client.post('/api/auth/login', json={
            'email': 'test@example.com',
            'password': 'wrong-password'
        })
    assert response.status_code == 429

def test_sql_injection(client, db_session):
    # Create user
    user = User(email='test@example.com', name='Test User')
    user.set_password('password123')
    db_session.add(user)
    db_session.commit()

    # Test SQL injection
    response = client.post('/api/auth/login', json={
        'email': "test@example.com' OR '1'='1",
        'password': "password123' OR '1'='1"
    })
    assert response.status_code == 401
```

## Test Reporting

### 1. Coverage Report

```python
# pytest.ini
[pytest]
addopts = --cov=app --cov-report=html --cov-report=term-missing
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

### 2. Test Report

```python
# tests/utils/report.py
import json
from datetime import datetime

class TestReport:
    def __init__(self):
        self.results = {
            'timestamp': datetime.utcnow().isoformat(),
            'total': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'duration': 0,
            'tests': []
        }

    def add_result(self, test_id, status, duration, error=None):
        self.results['tests'].append({
            'id': test_id,
            'status': status,
            'duration': duration,
            'error': str(error) if error else None
        })
        self.results['total'] += 1
        self.results[status.lower()] += 1
        self.results['duration'] += duration

    def save(self, filename):
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
```

## Best Practices

1. **Test Organization**:
   - Use clear test names
   - Group related tests
   - Use appropriate fixtures
   - Follow AAA pattern

2. **Data Management**:
   - Use test databases
   - Clean up test data
   - Use transactions
   - Mock external services

3. **Coverage**:
   - Aim for high coverage
   - Test edge cases
   - Test error conditions
   - Test security features

4. **Performance**:
   - Keep tests fast
   - Use appropriate tools
   - Monitor test duration
   - Parallelize when possible

## Troubleshooting

1. **Test Failures**:
   - Check test data
   - Verify dependencies
   - Review error messages
   - Check environment

2. **Performance Issues**:
   - Optimize slow tests
   - Use appropriate tools
   - Monitor resources
   - Review test design

3. **Coverage Gaps**:
   - Review coverage report
   - Add missing tests
   - Test edge cases
   - Verify critical paths

## Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Coverage Documentation](https://coverage.readthedocs.io/)
- [Locust Documentation](https://docs.locust.io/)
- [Selenium Documentation](https://www.selenium.dev/documentation/)
