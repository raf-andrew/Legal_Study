# Contributing to Legal Study Console Control

Thank you for your interest in contributing to the Legal Study Console Control! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please be respectful and considerate of others.

## How to Contribute

1. Fork the repository
2. Create a new branch for your feature or bugfix
3. Make your changes
4. Run the test suite
5. Submit a pull request

## Development Setup

1. Clone your fork:
```bash
git clone https://github.com/your-username/legal-study-console.git
cd legal-study-console
```

2. Install dependencies:
```bash
composer install
```

3. Run tests:
```bash
composer test
```

## Coding Standards

We follow PSR-12 coding standards. Please ensure your code adheres to these standards:

```bash
composer cs
```

## Testing

All contributions must include tests. We use PHPUnit for testing:

```bash
composer test
```

## Static Analysis

We use PHPStan for static analysis:

```bash
composer stan
```

## Documentation

Please ensure all new features are documented in:
- README.md
- PHPDoc blocks
- Any relevant documentation files

## Pull Request Process

1. Update the README.md with details of changes if needed
2. Update the documentation with any new features
3. The PR must pass all tests and checks
4. The PR must be reviewed by at least one maintainer

## Versioning

We use SemVer for versioning. For the versions available, see the tags on this repository.

## Questions?

If you have any questions, please open an issue in the repository. 