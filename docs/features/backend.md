# Backend Guide

This guide explains the backend system in the Legal Study Platform.

## Overview

The platform implements a robust backend system with support for:

- API endpoints
- Database models
- Authentication
- Business logic
- Background tasks
- Error handling

## API Endpoints

### 1. Route Configuration

```python
# app/routes/api.py
from flask import Blueprint, jsonify, request
from app.models import Document, User
from app.services import DocumentService, UserService
from app.middleware import auth_required, validate_request

api = Blueprint('api', __name__)

@api.route('/documents', methods=['GET'])
@auth_required
def get_documents():
    documents = DocumentService.get_all()
    return jsonify([doc.to_dict() for doc in documents])

@api.route('/documents/<int:id>', methods=['GET'])
@auth_required
def get_document(id):
    document = DocumentService.get_by_id(id)
    return jsonify(document.to_dict())

@api.route('/documents', methods=['POST'])
@auth_required
@validate_request
def create_document():
    data = request.get_json()
    document = DocumentService.create(data)
    return jsonify(document.to_dict()), 201

@api.route('/documents/<int:id>', methods=['PUT'])
@auth_required
@validate_request
def update_document(id):
    data = request.get_json()
    document = DocumentService.update(id, data)
    return jsonify(document.to_dict())

@api.route('/documents/<int:id>', methods=['DELETE'])
@auth_required
def delete_document(id):
    DocumentService.delete(id)
    return '', 204
```

### 2. Request Validation

```python
# app/middleware/validation.py
from functools import wraps
from flask import request, jsonify
from marshmallow import Schema, fields, validate, ValidationError

class DocumentSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    content = fields.Str(required=True)
    type = fields.Str(validate=validate.OneOf(['legal', 'contract', 'policy']))
    tags = fields.List(fields.Str())

def validate_request(schema: Schema):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                data = schema.load(request.get_json())
                request.validated_data = data
                return f(*args, **kwargs)
            except ValidationError as e:
                return jsonify({'error': str(e)}), 400
        return decorated_function
    return decorator
```

## Database Models

### 1. Base Model

```python
# app/models/base.py
from datetime import datetime
from app.extensions import db

class BaseModel(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def to_dict(self):
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
```

### 2. Document Model

```python
# app/models/document.py
from app.models.base import BaseModel
from app.extensions import db

class Document(BaseModel):
    __tablename__ = 'documents'

    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tags = db.relationship('Tag', secondary='document_tags')

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'title': self.title,
            'content': self.content,
            'type': self.type,
            'user_id': self.user_id,
            'tags': [tag.name for tag in self.tags]
        })
        return data
```

## Authentication

### 1. Authentication Service

```python
# app/services/auth.py
from datetime import datetime, timedelta
import jwt
from app.config import config
from app.models import User

class AuthService:
    @staticmethod
    def create_token(user_id: int) -> str:
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(days=1)
        }
        return jwt.encode(payload, config['jwt']['secret'])

    @staticmethod
    def verify_token(token: str) -> dict:
        try:
            payload = jwt.decode(token, config['jwt']['secret'])
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError('Token has expired')
        except jwt.InvalidTokenError:
            raise ValueError('Invalid token')

    @staticmethod
    def authenticate(email: str, password: str) -> User:
        user = User.query.filter_by(email=email).first()
        if not user or not user.verify_password(password):
            raise ValueError('Invalid credentials')
        return user
```

### 2. Authentication Middleware

```python
# app/middleware/auth.py
from functools import wraps
from flask import request, g, jsonify
from app.services.auth import AuthService

def auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'No authorization header'}), 401

        try:
            token = auth_header.split(' ')[1]
            payload = AuthService.verify_token(token)
            g.user_id = payload['user_id']
            return f(*args, **kwargs)
        except ValueError as e:
            return jsonify({'error': str(e)}), 401
    return decorated_function
```

## Business Logic

### 1. Document Service

```python
# app/services/document.py
from app.models import Document, Tag
from app.extensions import db

class DocumentService:
    @staticmethod
    def get_all():
        return Document.query.all()

    @staticmethod
    def get_by_id(id: int) -> Document:
        document = Document.query.get_or_404(id)
        return document

    @staticmethod
    def create(data: dict) -> Document:
        document = Document(
            title=data['title'],
            content=data['content'],
            type=data.get('type'),
            user_id=g.user_id
        )

        if 'tags' in data:
            tags = [Tag.get_or_create(name) for name in data['tags']]
            document.tags = tags

        document.save()
        return document

    @staticmethod
    def update(id: int, data: dict) -> Document:
        document = DocumentService.get_by_id(id)

        document.title = data['title']
        document.content = data['content']
        document.type = data.get('type')

        if 'tags' in data:
            tags = [Tag.get_or_create(name) for name in data['tags']]
            document.tags = tags

        document.save()
        return document

    @staticmethod
    def delete(id: int):
        document = DocumentService.get_by_id(id)
        document.delete()
```

### 2. User Service

```python
# app/services/user.py
from app.models import User
from app.extensions import db

class UserService:
    @staticmethod
    def create(data: dict) -> User:
        user = User(
            email=data['email'],
            name=data['name']
        )
        user.set_password(data['password'])
        user.save()
        return user

    @staticmethod
    def update(id: int, data: dict) -> User:
        user = User.query.get_or_404(id)

        if 'name' in data:
            user.name = data['name']
        if 'password' in data:
            user.set_password(data['password'])

        user.save()
        return user

    @staticmethod
    def delete(id: int):
        user = User.query.get_or_404(id)
        user.delete()
```

## Background Tasks

### 1. Task Queue

```python
# app/tasks/queue.py
from celery import Celery
from app.config import config

celery = Celery(
    'app',
    broker=config['celery']['broker_url'],
    backend=config['celery']['result_backend']
)

@celery.task
def process_document(document_id: int):
    from app.services import DocumentService
    document = DocumentService.get_by_id(document_id)
    # Process document...
    return {'status': 'success', 'document_id': document_id}
```

### 2. Task Handlers

```python
# app/tasks/handlers.py
from app.tasks.queue import celery
from app.services import NotificationService

@celery.task
def send_notification(user_id: int, message: str):
    NotificationService.send(user_id, message)

@celery.task
def cleanup_old_documents():
    from app.models import Document
    from datetime import datetime, timedelta

    old_documents = Document.query.filter(
        Document.created_at < datetime.utcnow() - timedelta(days=365)
    ).all()

    for document in old_documents:
        document.delete()
```

## Error Handling

### 1. Error Handlers

```python
# app/errors/handlers.py
from flask import jsonify
from werkzeug.exceptions import HTTPException
from app.extensions import db

def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad request',
            'message': str(error)
        }), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication required'
        }), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'error': 'Forbidden',
            'message': 'Permission denied'
        }), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not found',
            'message': 'Resource not found'
        }), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        db.session.rollback()
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500
```

### 2. Custom Exceptions

```python
# app/errors/exceptions.py
class ValidationError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class AuthenticationError(Exception):
    def __init__(self, message: str = 'Authentication failed'):
        self.message = message
        super().__init__(self.message)

class PermissionError(Exception):
    def __init__(self, message: str = 'Permission denied'):
        self.message = message
        super().__init__(self.message)
```

## Best Practices

1. **API Design**:
   - Use RESTful principles
   - Implement proper validation
   - Handle errors consistently
   - Use appropriate status codes

2. **Database**:
   - Use migrations
   - Implement proper indexes
   - Handle relationships
   - Use transactions

3. **Authentication**:
   - Use secure tokens
   - Implement proper validation
   - Handle permissions
   - Log security events

4. **Background Tasks**:
   - Use task queues
   - Handle failures
   - Monitor task status
   - Implement retries

## Troubleshooting

1. **API Issues**:
   - Check request validation
   - Verify authentication
   - Review error logs
   - Test endpoints

2. **Database Issues**:
   - Check migrations
   - Verify indexes
   - Monitor performance
   - Review queries

3. **Task Issues**:
   - Check task queue
   - Monitor workers
   - Review task logs
   - Handle failures

## Additional Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [JWT Documentation](https://jwt.io/)
