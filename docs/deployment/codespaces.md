# GitHub Codespaces

This guide explains how to use GitHub Codespaces for development in the Legal Study Platform.

## Overview

GitHub Codespaces provides a complete development environment in the cloud. It includes:

- Pre-configured development environment
- Integrated terminal
- Git integration
- Port forwarding
- Extensions support
- Persistent storage

## Getting Started

### Prerequisites

1. GitHub account with access to the repository
2. GitHub CLI installed locally
3. Docker installed locally (for local development)

### Creating a Codespace

1. Using the GitHub CLI:
   ```bash
   ./scripts/codespace create
   ```

2. Using the GitHub Web Interface:
   - Navigate to the repository
   - Click the "Code" button
   - Select the "Codespaces" tab
   - Click "Create codespace on main"

### Managing Codespaces

List all codespaces:
```bash
./scripts/codespace list
```

Delete a codespace:
```bash
./scripts/codespace delete <name>
```

Open a codespace in browser:
```bash
./scripts/codespace open <name>
```

Run a command in a codespace:
```bash
./scripts/codespace run <name> <command>
```

## Development Workflow

1. **Start Development**:
   ```bash
   ./scripts/start-dev.sh
   ```

2. **Run Tests**:
   ```bash
   ./scripts/run-tests.sh
   ```

3. **Build Documentation**:
   ```bash
   ./scripts/build-docs.sh
   ```

## Configuration

The Codespaces environment is configured through:

- `.codespaces/devcontainer.json` - Development container configuration
- `docker/Dockerfile.dev` - Development Dockerfile
- `.github/workflows/codespace-deploy.yml` - Deployment workflow

### Customizing the Environment

1. Modify `.codespaces/devcontainer.json` to:
   - Add extensions
   - Configure settings
   - Set up port forwarding
   - Install additional tools

2. Update `docker/Dockerfile.dev` to:
   - Install system dependencies
   - Configure development tools
   - Set up user permissions

## Best Practices

1. **Security**:
   - Never commit sensitive data
   - Use environment variables for secrets
   - Keep dependencies updated
   - Follow security best practices

2. **Performance**:
   - Use appropriate machine size
   - Clean up unused resources
   - Optimize Docker layers
   - Cache dependencies

3. **Collaboration**:
   - Share codespace configurations
   - Document environment setup
   - Use consistent coding standards
   - Review code changes

## Troubleshooting

Common issues and solutions:

1. **Codespace Creation Fails**:
   - Check repository permissions
   - Verify GitHub CLI authentication
   - Ensure sufficient quota

2. **Build Errors**:
   - Check Docker configuration
   - Verify dependencies
   - Review build logs

3. **Performance Issues**:
   - Increase machine size
   - Clean up disk space
   - Optimize Docker images

## Additional Resources

- [GitHub Codespaces Documentation](https://docs.github.com/en/codespaces)
- [Dev Container Specification](https://containers.dev/implementors/spec/)
- [GitHub CLI Documentation](https://cli.github.com/manual/)
- [Docker Documentation](https://docs.docker.com/)
