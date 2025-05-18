# Legal Study Platform Setup System

This directory contains scripts and configuration files for setting up and deploying the Legal Study Platform. The setup system provides a comprehensive solution for initializing the platform in various environments, including local development, GitHub Codespaces, and AWS cloud deployment.

## Directory Structure

```
.setup/
├── config/             # Configuration files
├── docs/              # Documentation files
├── logs/              # Setup and deployment logs
├── scripts/           # Setup and deployment scripts
├── tests/             # Setup system tests
├── diagrams/          # Architecture diagrams
├── main.py           # Main setup script
└── requirements.txt   # Setup dependencies
```

## Features

- Interactive setup process with configuration options
- Support for multiple deployment environments:
  - Local development
  - GitHub Codespaces
  - AWS cloud deployment
- Comprehensive testing infrastructure
- Automated documentation generation
- PlantUML architecture diagrams
- Configuration persistence and reuse

## Usage

### Interactive Setup

To run the interactive setup process:

```bash
python .setup/main.py --interactive
```

This will guide you through:
1. Selecting the deployment environment
2. Configuring the database
3. Setting up the API
4. Configuring testing options
5. Setting up documentation

### Using Existing Configuration

To use an existing configuration file:

```bash
python .setup/main.py --config path/to/config.json
```

### Individual Components

You can run individual setup components:

```bash
# Environment setup
python .setup/scripts/environment_setup.py

# Database setup
python .setup/scripts/database_setup.py

# API setup
python .setup/scripts/api_setup.py

# Test setup
python .setup/scripts/test_setup.py

# Documentation setup
python .setup/scripts/docs_setup.py
```

## Configuration

The setup system uses a JSON configuration file that includes:

```json
{
    "environment": "local|codespaces|aws",
    "database": {
        "type": "postgresql|mysql",
        "host": "localhost",
        "port": "5432",
        "name": "legal_study",
        "user": "username",
        "password": "password"
    },
    "api": {
        "port": "5000",
        "debug": true
    },
    "testing": {
        "run_unit_tests": true,
        "run_integration_tests": true,
        "generate_coverage": true
    },
    "documentation": {
        "generate_docs": true,
        "generate_diagrams": true
    }
}
```

## Testing

The setup system includes tests for all components:

```bash
# Run all setup tests
pytest .setup/tests/

# Run specific test categories
pytest .setup/tests/test_environment_setup.py
pytest .setup/tests/test_database_setup.py
pytest .setup/tests/test_api_setup.py
pytest .setup/tests/test_test_setup.py
pytest .setup/tests/test_docs_setup.py
```

## Documentation

The setup system generates comprehensive documentation:

- API documentation
- Architecture diagrams
- Deployment guides
- Development guidelines
- Testing documentation

To generate documentation:

```bash
python .setup/scripts/docs_setup.py
```

The documentation will be available in the `docs/` directory and can be viewed using MkDocs:

```bash
mkdocs serve
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
