# API Documentation

This guide documents the Legal Study Platform API.

## Overview

The API follows RESTful principles and uses JSON for data exchange.

### Base URL

```
http://localhost:8000/api
```

### Authentication

All API requests require authentication using JWT tokens.

```bash
Authorization: Bearer your-token
```

### Response Format

```json
{
  "data": {
    // Response data
  },
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 100
  },
  "links": {
    "first": "http://localhost:8000/api/resource?page=1",
    "last": "http://localhost:8000/api/resource?page=5",
    "prev": null,
    "next": "http://localhost:8000/api/resource?page=2"
  }
}
```

### Error Format

```json
{
  "error": {
    "code": "validation_error",
    "message": "Invalid input",
    "details": {
      "field": ["Error message"]
    }
  }
}
```

## Authentication

### Register

```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your-password",
  "name": "John Doe"
}
```

Response:
```json
{
  "data": {
    "user": {
      "id": 1,
      "email": "user@example.com",
      "name": "John Doe"
    },
    "token": "jwt-token"
  }
}
```

### Login

```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your-password"
}
```

Response:
```json
{
  "data": {
    "user": {
      "id": 1,
      "email": "user@example.com",
      "name": "John Doe"
    },
    "token": "jwt-token"
  }
}
```

### Refresh Token

```http
POST /auth/refresh
Authorization: Bearer your-token
```

Response:
```json
{
  "data": {
    "token": "new-jwt-token"
  }
}
```

### Logout

```http
POST /auth/logout
Authorization: Bearer your-token
```

Response:
```json
{
  "data": {
    "message": "Successfully logged out"
  }
}
```

## Documents

### List Documents

```http
GET /documents
Authorization: Bearer your-token
```

Query Parameters:
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20)
- `sort`: Sort field (default: created_at)
- `order`: Sort order (asc/desc)
- `search`: Search query
- `type`: Document type
- `status`: Document status

Response:
```json
{
  "data": {
    "documents": [
      {
        "id": 1,
        "title": "Legal Document",
        "type": "contract",
        "status": "active",
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:00Z"
      }
    ]
  },
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 100
  },
  "links": {
    "first": "http://localhost:8000/api/documents?page=1",
    "last": "http://localhost:8000/api/documents?page=5",
    "prev": null,
    "next": "http://localhost:8000/api/documents?page=2"
  }
}
```

### Get Document

```http
GET /documents/{id}
Authorization: Bearer your-token
```

Response:
```json
{
  "data": {
    "document": {
      "id": 1,
      "title": "Legal Document",
      "type": "contract",
      "status": "active",
      "content": "Document content",
      "metadata": {
        "author": "John Doe",
        "date": "2023-01-01"
      },
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T00:00:00Z"
    }
  }
}
```

### Create Document

```http
POST /documents
Authorization: Bearer your-token
Content-Type: multipart/form-data

file: @document.pdf
title: Legal Document
type: contract
description: Important legal document
```

Response:
```json
{
  "data": {
    "document": {
      "id": 1,
      "title": "Legal Document",
      "type": "contract",
      "status": "active",
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T00:00:00Z"
    }
  }
}
```

### Update Document

```http
PUT /documents/{id}
Authorization: Bearer your-token
Content-Type: application/json

{
  "title": "Updated Title",
  "description": "Updated description"
}
```

Response:
```json
{
  "data": {
    "document": {
      "id": 1,
      "title": "Updated Title",
      "type": "contract",
      "status": "active",
      "description": "Updated description",
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T00:00:00Z"
    }
  }
}
```

### Delete Document

```http
DELETE /documents/{id}
Authorization: Bearer your-token
```

Response:
```json
{
  "data": {
    "message": "Document deleted successfully"
  }
}
```

## Analysis

### Analyze Document

```http
POST /analysis
Authorization: Bearer your-token
Content-Type: application/json

{
  "document_id": 1,
  "analysis_type": "full"
}
```

Response:
```json
{
  "data": {
    "analysis": {
      "id": 1,
      "document_id": 1,
      "type": "full",
      "status": "processing",
      "created_at": "2023-01-01T00:00:00Z"
    }
  }
}
```

### Get Analysis

```http
GET /analysis/{id}
Authorization: Bearer your-token
```

Response:
```json
{
  "data": {
    "analysis": {
      "id": 1,
      "document_id": 1,
      "type": "full",
      "status": "completed",
      "results": {
        "entities": [
          {
            "type": "person",
            "text": "John Doe",
            "confidence": 0.95
          }
        ],
        "sentiments": [
          {
            "text": "Positive statement",
            "score": 0.8
          }
        ]
      },
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T00:00:00Z"
    }
  }
}
```

### Export Analysis

```http
GET /analysis/{id}/export
Authorization: Bearer your-token
```

Response:
```json
{
  "data": {
    "export": {
      "url": "http://localhost:8000/storage/exports/analysis-1.pdf",
      "expires_at": "2023-01-02T00:00:00Z"
    }
  }
}
```

## Search

### Search Documents

```http
GET /documents/search
Authorization: Bearer your-token
```

Query Parameters:
- `q`: Search query
- `type`: Document type
- `date_from`: Start date
- `date_to`: End date
- `page`: Page number
- `per_page`: Items per page

Response:
```json
{
  "data": {
    "documents": [
      {
        "id": 1,
        "title": "Legal Document",
        "type": "contract",
        "status": "active",
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:00Z",
        "score": 0.95
      }
    ]
  },
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 100
  }
}
```

### Advanced Search

```http
POST /documents/search/advanced
Authorization: Bearer your-token
Content-Type: application/json

{
  "query": "legal",
  "filters": {
    "type": "contract",
    "date_range": {
      "start": "2023-01-01",
      "end": "2023-12-31"
    },
    "status": "active"
  },
  "page": 1,
  "per_page": 20
}
```

Response:
```json
{
  "data": {
    "documents": [
      {
        "id": 1,
        "title": "Legal Document",
        "type": "contract",
        "status": "active",
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:00Z",
        "score": 0.95
      }
    ]
  },
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 100
  }
}
```

## Error Codes

- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `422`: Validation Error
- `429`: Too Many Requests
- `500`: Internal Server Error

## Rate Limiting

- 60 requests per minute per IP
- 1000 requests per hour per user

## Versioning

API versioning is handled through the URL:

```
http://localhost:8000/api/v1/resource
```

## Additional Resources

- [API Reference](reference/api.md)
- [Authentication Guide](features/authentication.md)
- [Error Handling](reference/errors.md)
- [Rate Limiting](reference/rate-limiting.md)
