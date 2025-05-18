# Contributing to the Security Domain

First off, thank you for considering contributing to the security domain! It's people like you that make it such a great tool.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the issue list as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* Use a clear and descriptive title
* Describe the exact steps which reproduce the problem
* Provide specific examples to demonstrate the steps
* Describe the behavior you observed after following the steps
* Explain which behavior you expected to see instead and why
* Include screenshots and animated GIFs if possible
* Include error messages and stack traces
* Include the version of the code you're using

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* Use a clear and descriptive title
* Provide a step-by-step description of the suggested enhancement
* Provide specific examples to demonstrate the steps
* Describe the current behavior and explain which behavior you expected to see instead
* Explain why this enhancement would be useful
* List some other tools or applications where this enhancement exists
* Include screenshots and animated GIFs if relevant

### Pull Requests

* Fill in the required template
* Do not include issue numbers in the PR title
* Follow the Python style guide
* Include screenshots and animated GIFs in your pull request whenever possible
* Document new code
* End all files with a newline

## Development Process

1. Fork the repository
2. Create a new branch for your feature
3. Make your changes
4. Write or update tests
5. Update documentation
6. Submit a pull request

### Setting Up Development Environment

```bash
# Clone your fork
git clone git@github.com:your-username/sniffing.git

# Add upstream remote
git remote add upstream git@github.com:original/sniffing.git

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest test_security.py

# Run with coverage
pytest --cov=sniffing tests/
```

### Code Style

We use several tools to maintain code quality:

* black for code formatting
* flake8 for style guide enforcement
* mypy for type checking
* isort for import sorting

```bash
# Format code
black .

# Check style
flake8 .

# Check types
mypy .

# Sort imports
isort .
```

### Documentation

* Use docstrings for all public modules, functions, classes, and methods
* Follow the Google style for docstrings
* Keep the README.md up to date
* Update CHANGELOG.md for notable changes

### Security Considerations

When contributing to security features:

* Follow secure coding practices
* Update security patterns and rules
* Consider OWASP guidelines
* Include security tests
* Document security implications

### Commit Messages

* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line

### Branch Naming

* feature/: New features
* bugfix/: Bug fixes
* docs/: Documentation changes
* test/: Test-related changes
* refactor/: Code refactoring
* chore/: Maintenance tasks

## Additional Notes

### Issue and Pull Request Labels

* bug: Something isn't working
* enhancement: New feature or request
* documentation: Documentation-related changes
* good first issue: Good for newcomers
* help wanted: Extra attention is needed
* security: Security-related changes
* performance: Performance-related changes
* testing: Test-related changes

### Security Vulnerabilities

If you discover a security vulnerability, please send an email to security@example.com instead of opening an issue. Security vulnerabilities will be addressed promptly.

## Questions?

Feel free to contact the core team if you have any questions. We're here to help!
