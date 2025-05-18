# Legal Study Platform - Codespaces Setup

This directory contains the configuration and setup scripts for running the Legal Study Platform in GitHub Codespaces. The setup provides a complete development environment with all necessary services, monitoring, and testing infrastructure.

## Features

- Complete development environment with all required services
- Automatic service health checks and monitoring
- Comprehensive testing infrastructure
- Logging and auditing capabilities
- Self-healing mechanisms
- Easy switching between Codespaces and local development

## Directory Structure

```
.codespaces/
├── config/                 # Configuration files
│   ├── codespaces_config.yaml
│   └── prometheus.yml
├── scripts/               # Setup and utility scripts
│   └── setup_codespace.py
├── data/                  # Persistent data storage
├── logs/                  # Application logs
├── audit/                 # Audit logs
├── utils/                 # Utility scripts
├── tests/                 # Test files
├── docker-compose.yml     # Docker Compose configuration
├── Dockerfile.api         # API service Dockerfile
├── Dockerfile.frontend    # Frontend service Dockerfile
└── requirements.txt       # Python dependencies
```

## Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- Docker and Docker Compose
- GitHub Codespaces access

## Quick Start

1. Install Python dependencies:
   ```bash
   pip install -r .codespaces/requirements.txt
   ```

2. Run the setup script:
   ```bash
   python .codespaces/scripts/setup_codespace.py
   ```

The setup script will:
- Configure the environment
- Start all required services
- Run health checks
- Execute tests
- Set up monitoring

## Services

The setup includes the following services:

- API Service (FastAPI)
- Frontend Service (Vite + React)
- PostgreSQL Database
- Redis Cache
- RabbitMQ Message Queue
- Prometheus Monitoring
- Grafana Dashboards
- Elasticsearch
- Kibana

## Monitoring

The platform includes comprehensive monitoring through:

- Prometheus for metrics collection
- Grafana for visualization
- Health checks for all services
- Log aggregation with Elasticsearch
- Kibana for log analysis

## Testing

The setup includes various types of tests:

- Unit tests
- Integration tests
- Functional tests
- Performance tests
- Security tests

Run tests using:
```bash
pytest .codespaces/tests/
```

## Configuration

The main configuration file is `.codespaces/config/codespaces_config.yaml`. It includes settings for:

- Environment configuration
- Service configuration
- Monitoring setup
- Logging configuration
- Testing parameters
- Deployment settings
- Security settings
- Data retention policies
- Self-healing configuration

## Local Development

To run the platform locally:

1. Ensure Docker and Docker Compose are installed
2. Navigate to the project root
3. Run:
   ```bash
   docker-compose -f .codespaces/docker-compose.yml up -d
   ```

## Health Checks

Health checks are configured for all services. You can view the status at:

- API: http://localhost:8000/health
- Frontend: http://localhost:3000/health
- Grafana: http://localhost:3001
- Kibana: http://localhost:5601

## Logging

Logs are stored in the `.codespaces/logs` directory and can be viewed through:

- Kibana: http://localhost:5601
- Direct file access in `.codespaces/logs`

## Security

The setup includes:

- JWT authentication
- RBAC authorization
- Audit logging
- Secure service communication
- Non-root container users
- Health check endpoints

## Troubleshooting

Common issues and solutions:

1. Service not starting:
   - Check Docker logs: `docker-compose logs <service>`
   - Verify health checks
   - Check configuration files

2. Tests failing:
   - Ensure all services are running
   - Check test configuration
   - Verify dependencies

3. Monitoring issues:
   - Check Prometheus targets
   - Verify Grafana data sources
   - Check Elasticsearch health

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

This setup is part of the Legal Study Platform and is subject to the same license terms.

# Codespaces Testing Infrastructure

This directory contains the testing infrastructure for the application in GitHub Codespaces. The setup includes comprehensive test suites, verification systems, and documentation generation.

## Directory Structure

```
.codespaces/
├── config/                 # Configuration files
├── logs/                   # Test execution logs
├── complete/              # Completed test logs
├── verification/          # Verification results
├── docs/                  # Generated documentation
├── issues/                # Issue reports
├── scripts/               # Test and utility scripts
├── Dockerfile.api         # API service Dockerfile
├── Dockerfile.frontend    # Frontend service Dockerfile
└── docker-compose.yml     # Docker Compose configuration
```

## Test Suites

The testing infrastructure includes the following test suites:

1. **Feature Tests**
   - End-to-end functionality tests
   - User interaction tests
   - Business logic validation

2. **Unit Tests**
   - Individual component tests
   - Function and method tests
   - Isolated functionality tests

3. **Integration Tests**
   - Component interaction tests
   - Service integration tests
   - API integration tests

4. **Performance Tests**
   - Load testing
   - Stress testing
   - Response time testing

5. **Security Tests**
   - Authentication tests
   - Authorization tests
   - Security vulnerability tests

## Running Tests

To run all tests:

```bash
.codespaces/scripts/run_all_tests.sh
```

This script will:
1. Run all test suites in sequence
2. Verify test completion
3. Resolve any issues found
4. Generate documentation

## Test Verification

The verification system:
- Validates test execution
- Checks test coverage
- Verifies checklist completion
- Generates verification reports

## Issue Resolution

The issue resolution system:
- Identifies test failures
- Analyzes failure patterns
- Generates issue reports
- Provides resolution recommendations

## Documentation

The documentation system generates:
- Test execution reports
- Verification reports
- Issue resolution reports
- Summary documentation

## Configuration

Configuration files are located in `.codespaces/config/`:
- `codespaces_config.yaml`: Main configuration
- `unit_test_config.yaml`: Unit test configuration
- `codespaces_test_config.yaml`: Test suite configuration

## Docker Setup

The Docker configuration includes:
- API service container
- Frontend service container
- Database container
- Cache container

To start the services:

```bash
docker-compose up -d
```

## Logging

Logs are stored in `.codespaces/logs/`:
- Test execution logs
- Verification logs
- Issue resolution logs
- Documentation generation logs

## Checklist System

The checklist system tracks:
- Test completion status
- Verification status
- Issue resolution status
- Documentation status

## Best Practices

1. **Test Execution**
   - Run tests in sequence
   - Verify each test suite
   - Document any failures
   - Update checklists

2. **Issue Resolution**
   - Analyze failure patterns
   - Document resolution steps
   - Update verification status
   - Generate resolution reports

3. **Documentation**
   - Keep documentation up to date
   - Include all test results
   - Document any issues
   - Maintain checklists

## Troubleshooting

Common issues and solutions:

1. **Test Failures**
   - Check test logs in `.codespaces/logs/`
   - Review issue reports in `.codespaces/issues/`
   - Update checklists in `.test/`

2. **Verification Failures**
   - Check verification logs
   - Review verification reports
   - Update verification status

3. **Documentation Issues**
   - Check documentation logs
   - Review generated docs
   - Update documentation templates

## Contributing

When adding new tests or modifying the testing infrastructure:

1. Update relevant configuration files
2. Add new test suites to the run script
3. Update documentation templates
4. Maintain checklist items
5. Follow the established logging format

## Support

For issues or questions:
1. Check the logs in `.codespaces/logs/`
2. Review the documentation in `.codespaces/docs/`
3. Check the verification reports
4. Consult the issue resolution reports
