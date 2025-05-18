# Installation Guide

This guide explains how to install and set up the Legal Study Platform.

## Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- Docker and Docker Compose
- Git
- PostgreSQL 14 or higher (if not using Docker)
- 4GB RAM minimum
- 10GB free disk space

## Installation Methods

### 1. Using Docker (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/legal-study/legal-study.git
   cd legal-study
   ```

2. Copy environment file:
   ```bash
   cp .env.example .env
   ```

3. Start the platform:
   ```bash
   docker-compose up -d
   ```

4. Access the platform:
   - Web interface: http://localhost:8000
   - API: http://localhost:8000/api
   - Documentation: http://localhost:8000/docs

### 2. Manual Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/legal-study/legal-study.git
   cd legal-study
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   .\venv\Scripts\activate   # Windows
   ```

3. Install Python dependencies:
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

6. Set up database:
   ```bash
   ./scripts/setup-db.sh
   ```

7. Run migrations:
   ```bash
   ./scripts/migrate.sh
   ```

8. Load initial data:
   ```bash
   ./scripts/seed.sh
   ```

9. Start the platform:
   ```bash
   ./scripts/start.sh
   ```

### 3. Using GitHub Codespaces

1. Fork the repository
2. Open in GitHub Codespaces:
   - Go to repository
   - Click "Code"
   - Select "Codespaces" tab
   - Click "Create codespace on main"

3. Wait for environment setup

4. Access the platform:
   - Web interface: http://localhost:8000
   - API: http://localhost:8000/api
   - Documentation: http://localhost:8000/docs

## Configuration

### Environment Variables

Key environment variables:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/legal_study

# Security
SECRET_KEY=your-secret-key
JWT_SECRET=your-jwt-secret

# API
API_HOST=0.0.0.0
API_PORT=8000

# Frontend
FRONTEND_URL=http://localhost:3000

# Email
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=user@example.com
SMTP_PASSWORD=your-password

# Storage
STORAGE_PATH=/path/to/storage
```

### Database Configuration

1. PostgreSQL settings:
   ```ini
   max_connections = 100
   shared_buffers = 256MB
   effective_cache_size = 768MB
   maintenance_work_mem = 64MB
   checkpoint_completion_target = 0.9
   wal_buffers = 16MB
   default_statistics_target = 100
   random_page_cost = 1.1
   effective_io_concurrency = 200
   work_mem = 4MB
   min_wal_size = 1GB
   max_wal_size = 4GB
   ```

2. Create database:
   ```sql
   CREATE DATABASE legal_study;
   CREATE USER legal_study WITH PASSWORD 'your-password';
   GRANT ALL PRIVILEGES ON DATABASE legal_study TO legal_study;
   ```

### Security Configuration

1. Generate secrets:
   ```bash
   ./scripts/generate-secrets.sh
   ```

2. Configure SSL:
   ```bash
   ./scripts/setup-ssl.sh
   ```

3. Set up firewall:
   ```bash
   ./scripts/setup-firewall.sh
   ```

## Verification

1. Check installation:
   ```bash
   ./scripts/verify-install.sh
   ```

2. Run tests:
   ```bash
   ./scripts/run-tests.sh
   ```

3. Check services:
   ```bash
   ./scripts/check-services.sh
   ```

## Troubleshooting

### Common Issues

1. **Database Connection**:
   - Check PostgreSQL is running
   - Verify connection string
   - Check user permissions

2. **Port Conflicts**:
   - Check if ports are in use
   - Change ports in configuration
   - Stop conflicting services

3. **Dependency Issues**:
   - Update pip and npm
   - Clear cache
   - Check version compatibility

4. **Permission Issues**:
   - Check file permissions
   - Check directory permissions
   - Check user permissions

### Logs

1. Application logs:
   ```bash
   ./scripts/show-logs.sh
   ```

2. Database logs:
   ```bash
   ./scripts/show-db-logs.sh
   ```

3. System logs:
   ```bash
   ./scripts/show-system-logs.sh
   ```

## Updating

1. Pull latest changes:
   ```bash
   git pull origin main
   ```

2. Update dependencies:
   ```bash
   ./scripts/update-deps.sh
   ```

3. Run migrations:
   ```bash
   ./scripts/migrate.sh
   ```

4. Restart services:
   ```bash
   ./scripts/restart.sh
   ```

## Uninstallation

1. Stop services:
   ```bash
   ./scripts/stop.sh
   ```

2. Remove data:
   ```bash
   ./scripts/cleanup.sh
   ```

3. Remove installation:
   ```bash
   ./scripts/uninstall.sh
   ```

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Python Documentation](https://docs.python.org/)
- [Node.js Documentation](https://nodejs.org/docs/)
- [GitHub Codespaces Documentation](https://docs.github.com/en/codespaces)
