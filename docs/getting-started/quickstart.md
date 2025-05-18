# Quick Start Guide

This guide will help you get started with the Legal Study Platform quickly.

## Prerequisites

- Docker and Docker Compose
- Git
- 4GB RAM minimum
- 10GB free disk space

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/legal-study/legal-study.git
   cd legal-study
   ```

2. Start the platform:
   ```bash
   docker-compose up -d
   ```

3. Access the platform:
   - Web interface: http://localhost:8000
   - API: http://localhost:8000/api
   - Documentation: http://localhost:8000/docs

## Basic Usage

### 1. Authentication

1. Register a new account:
   ```bash
   curl -X POST http://localhost:8000/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com", "password": "your-password"}'
   ```

2. Login:
   ```bash
   curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com", "password": "your-password"}'
   ```

3. Use the token:
   ```bash
   curl -H "Authorization: Bearer your-token" http://localhost:8000/api/user/profile
   ```

### 2. Document Management

1. Upload a document:
   ```bash
   curl -X POST http://localhost:8000/api/documents \
     -H "Authorization: Bearer your-token" \
     -F "file=@document.pdf" \
     -F "title=Legal Document" \
     -F "description=Important legal document"
   ```

2. List documents:
   ```bash
   curl -H "Authorization: Bearer your-token" http://localhost:8000/api/documents
   ```

3. Get document details:
   ```bash
   curl -H "Authorization: Bearer your-token" http://localhost:8000/api/documents/1
   ```

### 3. Legal Analysis

1. Analyze a document:
   ```bash
   curl -X POST http://localhost:8000/api/analysis \
     -H "Authorization: Bearer your-token" \
     -H "Content-Type: application/json" \
     -d '{"document_id": 1, "analysis_type": "full"}'
   ```

2. Get analysis results:
   ```bash
   curl -H "Authorization: Bearer your-token" http://localhost:8000/api/analysis/1
   ```

3. Export analysis:
   ```bash
   curl -H "Authorization: Bearer your-token" http://localhost:8000/api/analysis/1/export
   ```

### 4. Search and Filter

1. Search documents:
   ```bash
   curl -H "Authorization: Bearer your-token" \
     "http://localhost:8000/api/documents/search?q=legal&type=contract"
   ```

2. Filter documents:
   ```bash
   curl -H "Authorization: Bearer your-token" \
     "http://localhost:8000/api/documents?status=active&category=contract"
   ```

3. Advanced search:
   ```bash
   curl -X POST http://localhost:8000/api/documents/search/advanced \
     -H "Authorization: Bearer your-token" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "legal",
       "filters": {
         "type": "contract",
         "date_range": {
           "start": "2023-01-01",
           "end": "2023-12-31"
         }
       }
     }'
   ```

## Common Tasks

### 1. User Management

1. Update profile:
   ```bash
   curl -X PUT http://localhost:8000/api/user/profile \
     -H "Authorization: Bearer your-token" \
     -H "Content-Type: application/json" \
     -d '{"name": "John Doe", "organization": "Legal Corp"}'
   ```

2. Change password:
   ```bash
   curl -X POST http://localhost:8000/api/user/change-password \
     -H "Authorization: Bearer your-token" \
     -H "Content-Type: application/json" \
     -d '{
       "current_password": "old-password",
       "new_password": "new-password"
     }'
   ```

### 2. Document Organization

1. Create folder:
   ```bash
   curl -X POST http://localhost:8000/api/folders \
     -H "Authorization: Bearer your-token" \
     -H "Content-Type: application/json" \
     -d '{"name": "Contracts", "parent_id": null}'
   ```

2. Move document:
   ```bash
   curl -X PUT http://localhost:8000/api/documents/1/move \
     -H "Authorization: Bearer your-token" \
     -H "Content-Type: application/json" \
     -d '{"folder_id": 1}'
   ```

### 3. Collaboration

1. Share document:
   ```bash
   curl -X POST http://localhost:8000/api/documents/1/share \
     -H "Authorization: Bearer your-token" \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": 2,
       "permission": "edit"
     }'
   ```

2. Add comment:
   ```bash
   curl -X POST http://localhost:8000/api/documents/1/comments \
     -H "Authorization: Bearer your-token" \
     -H "Content-Type: application/json" \
     -d '{"content": "Important note"}'
   ```

## Next Steps

1. **Explore Features**:
   - Read the [Features Guide](features/api.md)
   - Try the [API Reference](reference/api.md)
   - Check the [Configuration Guide](getting-started/configuration.md)

2. **Development**:
   - Set up [Development Environment](development/environment.md)
   - Read [Contributing Guide](development/contributing.md)
   - Learn about [Testing](development/testing.md)

3. **Deployment**:
   - Read [Deployment Guide](deployment/docker.md)
   - Learn about [GitHub Codespaces](deployment/codespaces.md)
   - Check [CI/CD Setup](deployment/ci-cd.md)

## Troubleshooting

1. **Platform Not Starting**:
   ```bash
   # Check logs
   docker-compose logs

   # Check services
   docker-compose ps

   # Restart services
   docker-compose restart
   ```

2. **API Errors**:
   ```bash
   # Check API status
   curl http://localhost:8000/api/health

   # Check API logs
   docker-compose logs api
   ```

3. **Database Issues**:
   ```bash
   # Check database
   docker-compose exec db psql -U legal_study

   # Check migrations
   ./scripts/migrate.sh status
   ```

## Additional Resources

- [API Documentation](http://localhost:8000/docs)
- [User Guide](user-guide/index.md)
- [Developer Guide](developer-guide/index.md)
- [FAQ](faq.md)
- [Support](support.md)
