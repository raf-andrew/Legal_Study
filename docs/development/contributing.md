# Contributing Guide

Thank you for your interest in contributing to the Legal Study Platform! This guide will help you get started.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/legal-study.git
   cd legal-study
   ```
3. Add upstream remote:
   ```bash
   git remote add upstream https://github.com/legal-study/legal-study.git
   ```
4. Create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

1. **Set up environment**:
   ```bash
   ./scripts/setup.sh
   ```

2. **Make changes**:
   - Write code
   - Add tests
   - Update documentation
   - Follow style guide

3. **Run tests**:
   ```bash
   ./scripts/run-tests.sh
   ```

4. **Check code quality**:
   ```bash
   ./scripts/lint.sh
   ./scripts/type-check.sh
   ```

5. **Commit changes**:
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

6. **Push changes**:
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create pull request**:
   - Go to GitHub
   - Click "New Pull Request"
   - Select your branch
   - Fill in template
   - Submit PR

## Pull Request Process

1. **Title**:
   - Use conventional commits format
   - Be descriptive
   - Keep it short

2. **Description**:
   - Explain changes
   - Link related issues
   - Include screenshots if UI changes
   - List testing done

3. **Checks**:
   - All tests pass
   - Code coverage maintained
   - Linting passes
   - Type checking passes
   - Documentation updated

4. **Review**:
   - Address feedback
   - Keep PR focused
   - Update as needed
   - Be responsive

## Code Style

### Python

- Follow PEP 8
- Use type hints
- Write docstrings
- Keep functions small
- Use meaningful names

Example:
```python
from typing import List, Optional

def process_documents(documents: List[Document],
                     options: Optional[Dict[str, Any]] = None) -> List[Result]:
    """Process a list of legal documents.

    Args:
        documents: List of documents to process
        options: Optional processing options

    Returns:
        List of processing results

    Raises:
        ValueError: If documents list is empty
    """
    if not documents:
        raise ValueError("Documents list cannot be empty")

    results = []
    for doc in documents:
        result = process_single_document(doc, options)
        results.append(result)

    return results
```

### JavaScript/TypeScript

- Follow ESLint rules
- Use TypeScript
- Write JSDoc comments
- Use meaningful names
- Keep functions pure

Example:
```typescript
/**
 * Process a legal document
 * @param document - The document to process
 * @param options - Processing options
 * @returns Processing result
 */
async function processDocument(
  document: Document,
  options?: ProcessingOptions
): Promise<Result> {
  if (!document) {
    throw new Error('Document is required');
  }

  const result = await processSingleDocument(document, options);
  return result;
}
```

## Testing

1. **Write tests**:
   - Unit tests
   - Integration tests
   - Functional tests
   - API tests

2. **Test coverage**:
   - Maintain or improve coverage
   - Test edge cases
   - Test error conditions
   - Test performance

3. **Test documentation**:
   - Document test setup
   - Document test data
   - Document test scenarios
   - Document test results

## Documentation

1. **Code documentation**:
   - Write docstrings
   - Add comments
   - Document parameters
   - Document return values

2. **API documentation**:
   - Document endpoints
   - Document request/response
   - Document errors
   - Document examples

3. **User documentation**:
   - Update README
   - Update guides
   - Add examples
   - Add screenshots

## Review Process

1. **Code review**:
   - Check code quality
   - Check test coverage
   - Check documentation
   - Check performance

2. **Security review**:
   - Check for vulnerabilities
   - Check for best practices
   - Check for compliance
   - Check for data protection

3. **Final review**:
   - Check all requirements
   - Check all tests
   - Check all documentation
   - Check all feedback

## Release Process

1. **Version bump**:
   ```bash
   ./scripts/bump-version.sh
   ```

2. **Changelog**:
   ```bash
   ./scripts/update-changelog.sh
   ```

3. **Release notes**:
   - List changes
   - List breaking changes
   - List new features
   - List bug fixes

4. **Deployment**:
   ```bash
   ./scripts/deploy.sh
   ```

## Additional Resources

- [GitHub Flow](https://guides.github.com/introduction/flow/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Python Style Guide](https://www.python.org/dev/peps/pep-0008/)
- [TypeScript Style Guide](https://google.github.io/styleguide/tsguide.html)
- [Testing Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)
- [Documentation Best Practices](https://www.writethedocs.org/guide/)
