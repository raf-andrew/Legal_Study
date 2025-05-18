# Development Environment

This guide explains how to set up and use the development environment for the Legal Study Platform.

## Overview

The development environment includes:

- Python 3.11+ development environment
- Node.js 18+ for frontend development
- PostgreSQL database
- Docker for containerization
- GitHub Codespaces integration
- Testing and documentation tools

## Local Setup

### Prerequisites

1. Python 3.11 or higher
2. Node.js 18 or higher
3. Docker and Docker Compose
4. Git
5. GitHub CLI (optional, for Codespaces)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/legal-study/legal-study.git
   cd legal-study
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   .\venv\Scripts\activate   # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-test.txt
   ```

4. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   cd ..
   ```

5. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

### Database Setup

1. Start PostgreSQL using Docker:
   ```bash
   docker-compose up -d db
   ```

2. Run migrations:
   ```bash
   ./scripts/migrate.sh
   ```

3. Load initial data:
   ```bash
   ./scripts/seed.sh
   ```

## Development Workflow

### Starting the Development Server

1. Start the backend:
   ```bash
   ./scripts/start-dev.sh
   ```

2. Start the frontend (in a new terminal):
   ```bash
   cd frontend
   npm run dev
   ```

### Running Tests

1. Run all tests:
   ```bash
   ./scripts/run-tests.sh
   ```

2. Run specific test suites:
   ```bash
   pytest tests/unit/          # Unit tests
   pytest tests/integration/   # Integration tests
   pytest tests/functional/    # Functional tests
   ```

3. Generate coverage report:
   ```bash
   ./scripts/coverage.sh
   ```

### Code Quality

1. Run linters:
   ```bash
   ./scripts/lint.sh
   ```

2. Run type checking:
   ```bash
   ./scripts/type-check.sh
   ```

3. Format code:
   ```bash
   ./scripts/format.sh
   ```

## Using GitHub Codespaces

1. Create a new codespace:
   ```bash
   ./scripts/codespace create
   ```

2. Open in browser:
   ```bash
   ./scripts/codespace open <name>
   ```

3. Run commands:
   ```bash
   ./scripts/codespace run <name> <command>
   ```

## IDE Setup

### VS Code

1. Install recommended extensions:
   - Python
   - Pylance
   - Docker
   - GitLens
   - ESLint
   - Prettier

2. Configure settings:
   ```json
   {
     "python.linting.enabled": true,
     "python.linting.pylintEnabled": true,
     "python.formatting.provider": "black",
     "editor.formatOnSave": true,
     "editor.codeActionsOnSave": {
       "source.organizeImports": true
     }
   }
   ```

### PyCharm

1. Configure Python interpreter:
   - Use the virtual environment
   - Set up code style
   - Configure run configurations

2. Install plugins:
   - Docker
   - GitToolBox
   - Markdown
   - Database Tools

## Best Practices

1. **Code Style**:
   - Follow PEP 8
   - Use type hints
   - Write docstrings
   - Keep functions small

2. **Testing**:
   - Write unit tests
   - Use test fixtures
   - Mock external services
   - Maintain high coverage

3. **Git Workflow**:
   - Use feature branches
   - Write clear commit messages
   - Keep PRs small
   - Review code changes

4. **Documentation**:
   - Update docstrings
   - Keep README current
   - Document API changes
   - Write clear comments

## Troubleshooting

Common issues and solutions:

1. **Database Connection**:
   - Check PostgreSQL is running
   - Verify connection string
   - Check user permissions

2. **Dependency Issues**:
   - Update pip and npm
   - Clear cache
   - Check version compatibility

3. **Test Failures**:
   - Check test database
   - Verify test data
   - Check environment variables

## Additional Resources

- [Python Documentation](https://docs.python.org/)
- [Node.js Documentation](https://nodejs.org/docs/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Docker Documentation](https://docs.docker.com/)
- [VS Code Documentation](https://code.visualstudio.com/docs)
- [PyCharm Documentation](https://www.jetbrains.com/pycharm/documentation/)
