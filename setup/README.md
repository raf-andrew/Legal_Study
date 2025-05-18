# Legal Study Platform Setup

This directory contains the setup system for the Legal Study Platform. The setup system provides an interactive, guided process to configure and verify all components of the platform.

## Features

- Interactive setup process with clear progress indicators
- Environment validation (Python, Node.js, Docker)
- AWS integration and credential management
- Docker service setup and health checks
- GitHub integration and repository configuration
- Comprehensive health checks and status reporting
- Configuration management and persistence

## Directory Structure

```
setup/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── scripts/           # Setup and utility scripts
│   ├── setup.py       # Main setup script
│   └── check_docker_health.py  # Docker health checker
├── config/            # Configuration files
│   ├── setup_config.yaml      # Default configuration
│   ├── aws_config.json        # AWS credentials
│   └── github_config.json     # GitHub configuration
├── templates/         # Configuration templates
└── checks/           # Health check results
```

## Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- Docker 20.10 or higher
- Docker Compose 2.0 or higher
- AWS CLI (for AWS integration)
- Git (for GitHub integration)

## Installation

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the setup script:
   ```bash
   python scripts/setup.py
   ```

## Setup Process

The setup process will guide you through the following steps:

1. **Environment Check**
   - Verifies Python, Node.js, and Docker versions
   - Checks for required system dependencies

2. **AWS Configuration**
   - Prompts for AWS credentials
   - Verifies AWS access
   - Configures AWS services

3. **Docker Setup**
   - Builds Docker services
   - Starts containers
   - Runs health checks

4. **GitHub Integration**
   - Configures GitHub credentials
   - Sets up repository connection
   - Configures branch protection

## Health Checks

The setup system includes comprehensive health checks for:

- Docker containers
- Service endpoints
- Port availability
- AWS services
- GitHub connectivity

Health check results are stored in the `checks/` directory for future reference.

## Configuration

The setup system uses YAML configuration files for default settings. You can modify these files to customize the setup process:

- `config/setup_config.yaml`: Main configuration file
- `config/aws_config.json`: AWS-specific settings
- `config/github_config.json`: GitHub-specific settings

## Troubleshooting

If you encounter issues during setup:

1. Check the health check results in `checks/`
2. Verify your credentials and permissions
3. Ensure all prerequisites are met
4. Check the Docker logs for service issues

## Security

- Credentials are stored securely in configuration files
- AWS credentials are verified before use
- GitHub tokens are validated
- Docker health checks ensure service security

## Contributing

To contribute to the setup system:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This setup system is part of the Legal Study Platform and is subject to the same license terms.
