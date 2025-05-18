# Testing Guide

This guide explains the testing infrastructure and practices for the Legal Study Platform.

## Overview

The testing infrastructure includes:

- Unit tests
- Integration tests
- Functional tests
- API tests
- Performance tests
- Security tests
- Documentation tests

## Test Structure

```
tests/
├── unit/              # Unit tests
├── integration/       # Integration tests
├── functional/        # Functional tests
├── api/              # API tests
├── performance/      # Performance tests
├── security/         # Security tests
├── docs/             # Documentation tests
└── fixtures/         # Test fixtures
```

## Running Tests

### All Tests

```bash
./scripts/run-tests.sh
```

### Specific Test Suites

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Functional tests
pytest tests/functional/

# API tests
pytest tests/api/

# Performance tests
pytest tests/performance/

# Security tests
pytest tests/security/

# Documentation tests
pytest tests/docs/
```

### Test Options

```bash
# Run with coverage
pytest --cov=src tests/

# Run with verbose output
pytest -v tests/

# Run specific test file
pytest tests/unit/test_auth.py

# Run specific test function
pytest tests/unit/test_auth.py::test_login_success

# Run tests in parallel
pytest -n auto tests/
```

## Test Types

### Unit Tests

- Test individual components
- Mock external dependencies
- Fast execution
- High coverage

Example:
```python
def test_user_creation():
    user = User(username="test", email="test@example.com")
    assert user.username == "test"
    assert user.email == "test@example.com"
```

### Integration Tests

- Test component interactions
- Use test database
- Mock external services
- Medium execution time

Example:
```python
def test_user_auth_flow():
    # Create user
    user = create_test_user()

    # Test login
    token = login_user(user)
    assert token is not None

    # Test protected endpoint
    response = client.get("/api/user/profile", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
```

### Functional Tests

- Test complete features
- Use real database
- End-to-end testing
- Longer execution time

Example:
```python
def test_legal_document_workflow():
    # Create document
    doc = create_test_document()

    # Add annotations
    add_annotations(doc)

    # Generate report
    report = generate_report(doc)

    # Verify results
    assert report.status == "completed"
    assert len(report.annotations) > 0
```

### API Tests

- Test API endpoints
- Verify responses
- Check error handling
- Test rate limiting

Example:
```python
def test_api_endpoints():
    # Test GET endpoint
    response = client.get("/api/documents")
    assert response.status_code == 200
    assert "documents" in response.json()

    # Test POST endpoint
    response = client.post("/api/documents", json={"title": "Test"})
    assert response.status_code == 201
    assert response.json()["title"] == "Test"
```

## Test Fixtures

### Database Fixtures

```python
@pytest.fixture
def db():
    # Set up test database
    db = create_test_db()
    yield db
    # Clean up
    db.drop_all()
```

### Authentication Fixtures

```python
@pytest.fixture
def auth_client():
    # Create authenticated client
    client = create_test_client()
    token = get_test_token()
    client.headers = {"Authorization": f"Bearer {token}"}
    return client
```

## Best Practices

1. **Test Organization**:
   - Group related tests
   - Use descriptive names
   - Follow AAA pattern (Arrange, Act, Assert)
   - Keep tests independent

2. **Test Data**:
   - Use fixtures
   - Clean up after tests
   - Use realistic data
   - Avoid hardcoding values

3. **Assertions**:
   - Be specific
   - Test edge cases
   - Verify error conditions
   - Check side effects

4. **Performance**:
   - Run tests in parallel
   - Use appropriate test types
   - Optimize slow tests
   - Monitor test duration

## Test Reports

### Coverage Reports

```bash
# Generate coverage report
./scripts/coverage.sh

# View coverage in browser
coverage html
```

### Test Reports

```bash
# Generate HTML report
pytest --html=report.html tests/

# Generate JUnit XML report
pytest --junitxml=report.xml tests/
```

## Continuous Integration

### GitHub Actions

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Run tests
        run: pytest tests/
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Troubleshooting

Common issues and solutions:

1. **Test Failures**:
   - Check test data
   - Verify dependencies
   - Check environment variables
   - Review test logs

2. **Slow Tests**:
   - Use appropriate test types
   - Optimize database operations
   - Run tests in parallel
   - Use test caching

3. **Coverage Issues**:
   - Add missing tests
   - Check test quality
   - Review coverage reports
   - Update test requirements

## Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [coverage.py Documentation](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)
- [Test-Driven Development](https://en.wikipedia.org/wiki/Test-driven_development)
