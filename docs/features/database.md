# Database Guide

This guide explains the database system in the Legal Study Platform.

## Overview

The platform uses PostgreSQL as its primary database with support for:

- Relational data storage
- Full-text search
- Data versioning
- Backup and recovery
- Data migration

## Database Schema

### 1. Core Tables

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Documents table
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    type VARCHAR(50),
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Analysis table
CREATE TABLE analysis (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    result JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tags table
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Document tags table
CREATE TABLE document_tags (
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (document_id, tag_id)
);
```

### 2. Search Tables

```sql
-- Search index table
CREATE TABLE search_index (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    content TSVECTOR NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create GIN index for full-text search
CREATE INDEX search_index_content_idx ON search_index USING GIN(content);
```

### 3. Version Tables

```sql
-- Document versions table
CREATE TABLE document_versions (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Analysis versions table
CREATE TABLE analysis_versions (
    id SERIAL PRIMARY KEY,
    analysis_id INTEGER REFERENCES analysis(id) ON DELETE CASCADE,
    result JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
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
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

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

### 2. User Model

```python
# app/models/user.py
from app.models.base import BaseModel
from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(BaseModel):
    __tablename__ = 'users'

    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    documents = db.relationship('Document', backref='user', lazy=True)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'email': self.email,
            'name': self.name
        })
        return data
```

### 3. Document Model

```python
# app/models/document.py
from app.models.base import BaseModel
from app.extensions import db

class Document(BaseModel):
    __tablename__ = 'documents'

    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    tags = db.relationship('Tag', secondary='document_tags', lazy='joined')
    versions = db.relationship('DocumentVersion', backref='document', lazy=True)
    analysis = db.relationship('Analysis', backref='document', lazy=True)

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

## Database Operations

### 1. Connection Management

```python
# app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import config

db = SQLAlchemy()

def init_db(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = config['database']['uri']
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

def get_engine():
    return create_engine(config['database']['uri'])

def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()
```

### 2. CRUD Operations

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
        return Document.query.get_or_404(id)

    @staticmethod
    def create(data: dict) -> Document:
        document = Document(
            title=data['title'],
            content=data['content'],
            type=data.get('type'),
            user_id=data['user_id']
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

### 3. Search Operations

```python
# app/services/search.py
from app.models import Document, SearchIndex
from app.extensions import db
from sqlalchemy import text

class SearchService:
    @staticmethod
    def search_documents(query: str, limit: int = 10):
        search_query = text("""
            SELECT d.*, ts_rank(si.content, to_tsquery('english', :query)) as rank
            FROM documents d
            JOIN search_index si ON d.id = si.document_id
            WHERE si.content @@ to_tsquery('english', :query)
            ORDER BY rank DESC
            LIMIT :limit
        """)

        result = db.session.execute(
            search_query,
            {'query': query, 'limit': limit}
        )

        return [Document.query.get(row.id) for row in result]

    @staticmethod
    def update_search_index(document_id: int):
        document = Document.query.get_or_404(document_id)

        # Create or update search index
        search_index = SearchIndex.query.filter_by(document_id=document_id).first()
        if not search_index:
            search_index = SearchIndex(document_id=document_id)

        search_index.content = text("to_tsvector('english', :content)").bindparams(
            content=f"{document.title} {document.content}"
        )
        search_index.save()
```

## Data Migration

### 1. Alembic Setup

```python
# migrations/env.py
from alembic import context
from app.extensions import db
from app.models import Base

config = context.config
target_metadata = Base.metadata

def run_migrations_online():
    connectable = db.engine
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()
```

### 2. Migration Example

```python
# migrations/versions/add_user_role.py
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('users', sa.Column('role', sa.String(50), nullable=False, server_default='user'))
    op.create_index('ix_users_role', 'users', ['role'])

def downgrade():
    op.drop_index('ix_users_role', 'users')
    op.drop_column('users', 'role')
```

## Backup and Recovery

### 1. Backup Script

```python
# scripts/backup.py
import subprocess
from datetime import datetime
from app.config import config

def backup_database():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'backup_{timestamp}.sql'

    command = [
        'pg_dump',
        '-h', config['database']['host'],
        '-U', config['database']['user'],
        '-d', config['database']['name'],
        '-f', f'backups/{filename}'
    ]

    subprocess.run(command, check=True)
    return filename
```

### 2. Recovery Script

```python
# scripts/recover.py
import subprocess
from app.config import config

def recover_database(backup_file: str):
    command = [
        'psql',
        '-h', config['database']['host'],
        '-U', config['database']['user'],
        '-d', config['database']['name'],
        '-f', f'backups/{backup_file}'
    ]

    subprocess.run(command, check=True)
```

## Performance Optimization

### 1. Indexing

```sql
-- Create indexes for common queries
CREATE INDEX ix_documents_user_id ON documents(user_id);
CREATE INDEX ix_documents_type ON documents(type);
CREATE INDEX ix_documents_created_at ON documents(created_at);
CREATE INDEX ix_analysis_document_id ON analysis(document_id);
CREATE INDEX ix_document_tags_document_id ON document_tags(document_id);
CREATE INDEX ix_document_tags_tag_id ON document_tags(tag_id);
```

### 2. Query Optimization

```python
# app/services/document.py
from sqlalchemy.orm import joinedload

class DocumentService:
    @staticmethod
    def get_recent_documents(limit: int = 10):
        return Document.query\
            .options(joinedload(Document.tags))\
            .order_by(Document.created_at.desc())\
            .limit(limit)\
            .all()
```

### 3. Connection Pooling

```python
# app/extensions.py
from sqlalchemy.pool import QueuePool

def init_db(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = config['database']['uri']
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'poolclass': QueuePool,
        'pool_size': 10,
        'max_overflow': 20,
        'pool_timeout': 30,
        'pool_recycle': 1800
    }
    db.init_app(app)
```

### 4. Caching

```python
# app/services/cache.py
from functools import wraps
from app.extensions import redis_client

def cache_result(expire: int = 300):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            key = f"{f.__name__}:{str(args)}:{str(kwargs)}"
            result = redis_client.get(key)

            if result is None:
                result = f(*args, **kwargs)
                redis_client.setex(key, expire, result)

            return result
        return decorated_function
    return decorator
```

## Monitoring

### 1. Database Metrics

```python
# app/monitoring/database.py
from prometheus_client import Counter, Histogram
from app.extensions import db

# Metrics
db_operation_count = Counter(
    'db_operation_count',
    'Number of database operations',
    ['operation']
)

db_operation_duration = Histogram(
    'db_operation_duration_seconds',
    'Duration of database operations',
    ['operation']
)

# Middleware
def track_db_operations():
    @db.event.listens_for(db.session, 'after_commit')
    def after_commit(session):
        db_operation_count.labels('commit').inc()

    @db.event.listens_for(db.session, 'after_rollback')
    def after_rollback(session):
        db_operation_count.labels('rollback').inc()
```

### 2. Health Checks

```python
# app/health/database.py
from app.extensions import db

def check_database_health():
    try:
        db.session.execute('SELECT 1')
        return True
    except Exception:
        return False
```

### 3. Alerting

```python
# app/monitoring/alerts.py
from app.extensions import redis_client
from app.services import NotificationService

def check_database_alerts():
    # Check connection pool
    pool_size = db.engine.pool.size()
    if pool_size > 0.8 * db.engine.pool.maxsize:
        NotificationService.send_alert(
            'Database connection pool is near capacity',
            {'pool_size': pool_size}
        )

    # Check query performance
    slow_queries = db.session.execute("""
        SELECT query, calls, total_time
        FROM pg_stat_statements
        WHERE total_time > 1000
        ORDER BY total_time DESC
        LIMIT 5
    """).fetchall()

    if slow_queries:
        NotificationService.send_alert(
            'Slow database queries detected',
            {'queries': slow_queries}
        )
```

## Troubleshooting

1. **Connection Issues**:
   - Check database credentials
   - Verify network connectivity
   - Check connection pool settings
   - Review error logs

2. **Performance Issues**:
   - Analyze slow queries
   - Check index usage
   - Monitor connection pool
   - Review query plans

3. **Data Issues**:
   - Verify data integrity
   - Check constraints
   - Review foreign keys
   - Validate data types

## Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Database Best Practices](https://www.postgresql.org/docs/current/performance-tips.html)
