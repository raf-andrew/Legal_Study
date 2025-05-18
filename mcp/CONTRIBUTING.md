# Contributing to MCP

Thank you for your interest in contributing to the Master Control Program (MCP)! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please read it before contributing.

## Getting Started

1. Fork the repository
2. Clone your fork:
```bash
git clone https://github.com/your-username/mcp.git
cd mcp
```

3. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
```

4. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

5. Create feature branch:
```bash
git checkout -b feature/your-feature-name
```

## Development Process

1. **Code Style**
   - Follow PEP 8 guidelines
   - Use type hints
   - Write docstrings (Google style)
   - Keep functions focused and small
   - Use meaningful variable names

2. **Testing**
   - Write unit tests for new code
   - Update existing tests as needed
   - Maintain test coverage
   - Run full test suite before submitting

3. **Documentation**
   - Update README.md if needed
   - Add docstrings to new code
   - Update API documentation
   - Include examples for new features

4. **Commit Messages**
   - Use clear, descriptive messages
   - Reference issues and pull requests
   - Follow conventional commits format
   - Keep commits focused and atomic

## Pull Request Process

1. **Before Submitting**
   - Run tests: `pytest tests/`
   - Check code style: `black . && flake8 . && mypy .`
   - Update documentation
   - Rebase on main branch

2. **Pull Request Template**
   ```markdown
   ## Description
   Brief description of changes

   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update

   ## Testing
   Description of testing performed

   ## Checklist
   - [ ] Tests added/updated
   - [ ] Documentation updated
   - [ ] Code follows style guidelines
   - [ ] All tests passing
   ```

3. **Review Process**
   - Two approvals required
   - All comments addressed
   - All checks passing
   - Documentation updated

## Development Guidelines

### Code Organization

```
mcp/
├── server/
│   ├── orchestrator.py
│   ├── isolator.py
│   ├── analyzer.py
│   └── fixer.py
├── utils/
│   ├── config.py
│   ├── logging.py
│   ├── metrics.py
│   └── git.py
├── domains/
│   ├── security/
│   ├── browser/
│   ├── functional/
│   └── unit/
└── tests/
    ├── server/
    ├── utils/
    └── domains/
```

### Coding Standards

1. **Type Hints**
```python
def process_data(data: Dict[str, Any]) -> List[Result]:
    """Process input data.

    Args:
        data: Input data dictionary

    Returns:
        List of processing results
    """
    results: List[Result] = []
    # Process data
    return results
```

2. **Error Handling**
```python
try:
    result = process_data(data)
except ValueError as e:
    logger.error(f"Invalid data: {e}")
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
```

3. **Async/Await**
```python
async def process_files(
    files: List[str]
) -> Dict[str, Any]:
    """Process files asynchronously.

    Args:
        files: List of file paths

    Returns:
        Processing results
    """
    tasks = [process_file(file) for file in files]
    results = await asyncio.gather(*tasks)
    return {"files": len(files), "results": results}
```

4. **Configuration**
```python
class Config:
    """Configuration manager."""

    def __init__(self, path: str):
        """Initialize configuration.

        Args:
            path: Path to configuration file
        """
        self.path = path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        with open(self.path) as f:
            return yaml.safe_load(f)
```

### Testing Guidelines

1. **Unit Tests**
```python
def test_process_data():
    """Test data processing."""
    # Arrange
    data = {"key": "value"}

    # Act
    result = process_data(data)

    # Assert
    assert len(result) == 1
    assert result[0].key == "value"
```

2. **Integration Tests**
```python
@pytest.mark.asyncio
async def test_process_files():
    """Test file processing."""
    # Arrange
    files = ["file1.txt", "file2.txt"]

    # Act
    results = await process_files(files)

    # Assert
    assert results["files"] == 2
    assert len(results["results"]) == 2
```

3. **Mock Tests**
```python
@patch("mcp.utils.git.GitRepo")
def test_git_integration(mock_repo):
    """Test Git integration."""
    # Arrange
    mock_repo.return_value.get_files.return_value = ["file1.txt"]

    # Act
    git = GitIntegration(config)
    files = git.get_changed_files()

    # Assert
    assert len(files) == 1
    assert files[0] == "file1.txt"
```

## Release Process

1. **Version Bump**
   - Update version in setup.py
   - Update CHANGELOG.md
   - Create release branch

2. **Testing**
   - Run full test suite
   - Run integration tests
   - Check documentation

3. **Release**
   - Create release tag
   - Build distribution
   - Upload to PyPI
   - Update documentation

4. **Announcement**
   - Update release notes
   - Send notifications
   - Update documentation

## Getting Help

- Join our Discord server
- Check existing issues
- Read the documentation
- Ask in discussions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
