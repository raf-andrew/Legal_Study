#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import logging
from datetime import datetime
import json
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
import bcrypt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.testing/database_init.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class DatabaseInitializer:
    def __init__(self):
        self.workspace_root = Path(__file__).parent.parent
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'steps': {},
            'errors': []
        }
        
    def _get_database_url(self) -> str:
        """Get database URL from env file"""
        try:
            env_file = self.workspace_root / 'env.dev'
            with open(env_file) as f:
                for line in f:
                    if line.startswith('DATABASE_URL='):
                        return line.split('=', 1)[1].strip()
            raise ValueError("DATABASE_URL not found in env.dev")
        except Exception as e:
            self.results['errors'].append(f"Failed to get database URL: {str(e)}")
            raise
            
    def create_database(self) -> bool:
        """Create database if it doesn't exist"""
        try:
            database_url = self._get_database_url()
            engine = create_engine(database_url)
            
            # For SQLite, just ensure the directory exists
            db_path = Path(database_url.replace('sqlite:///', ''))
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                
            self.results['steps']['create_database'] = {
                'status': 'pass',
                'message': "Database exists and is accessible"
            }
            return engine
            
        except Exception as e:
            self.results['steps']['create_database'] = {
                'status': 'fail',
                'message': f"Failed to connect to database: {str(e)}"
            }
            self.results['errors'].append(str(e))
            return None
            
    def create_tables(self, engine) -> bool:
        """Create database tables"""
        try:
            with engine.begin() as conn:
                # Create users table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username VARCHAR(64) NOT NULL UNIQUE,
                        email VARCHAR(255) NOT NULL UNIQUE,
                        password_hash VARCHAR(255) NOT NULL,
                        is_active BOOLEAN NOT NULL DEFAULT 1,
                        is_admin BOOLEAN NOT NULL DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Create documents table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS documents (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title VARCHAR(255) NOT NULL,
                        content TEXT,
                        author_id INTEGER REFERENCES users(id),
                        is_public BOOLEAN NOT NULL DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Create comments table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS comments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        content TEXT NOT NULL,
                        document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
                        author_id INTEGER REFERENCES users(id),
                        parent_id INTEGER REFERENCES comments(id) ON DELETE CASCADE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Create tags table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS tags (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name VARCHAR(50) NOT NULL UNIQUE,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Create document_tags table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS document_tags (
                        document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
                        tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (document_id, tag_id)
                    )
                """))
                
                # Create alembic_version table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS alembic_version (
                        version_num VARCHAR(32) NOT NULL,
                        CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                    )
                """))
                
            self.results['steps']['create_tables'] = {
                'status': 'pass',
                'message': "Tables created successfully"
            }
            return True
            
        except Exception as e:
            self.results['steps']['create_tables'] = {
                'status': 'fail',
                'message': f"Failed to create tables: {str(e)}"
            }
            self.results['errors'].append(str(e))
            return False
            
    def create_admin_user(self, engine) -> bool:
        """Create admin user if it doesn't exist"""
        try:
            # Hash default admin password
            password = "admin123"  # This is just for testing
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(password.encode(), salt).decode()
            
            with engine.begin() as conn:
                # Check if admin exists
                result = conn.execute(
                    text("SELECT id FROM users WHERE username = 'admin'")
                ).fetchone()
                
                if not result:
                    # Create admin user
                    conn.execute(
                        text("""
                            INSERT INTO users (username, email, password_hash, is_admin)
                            VALUES (:username, :email, :password_hash, :is_admin)
                        """),
                        {
                            "username": "admin",
                            "email": "admin@example.com",
                            "password_hash": password_hash,
                            "is_admin": 1
                        }
                    )
                    
            self.results['steps']['create_admin'] = {
                'status': 'pass',
                'message': "Admin user created successfully"
            }
            return True
            
        except Exception as e:
            self.results['steps']['create_admin'] = {
                'status': 'fail',
                'message': f"Failed to create admin user: {str(e)}"
            }
            self.results['errors'].append(str(e))
            return False
            
    def set_initial_version(self, engine) -> bool:
        """Set initial alembic version"""
        try:
            with engine.begin() as conn:
                # Check if version exists
                result = conn.execute(
                    text("SELECT version_num FROM alembic_version")
                ).fetchone()
                
                if not result:
                    # Set initial version
                    conn.execute(
                        text("INSERT INTO alembic_version (version_num) VALUES ('initial')")
                    )
                    
            self.results['steps']['set_version'] = {
                'status': 'pass',
                'message': "Initial version set successfully"
            }
            return True
            
        except Exception as e:
            self.results['steps']['set_version'] = {
                'status': 'fail',
                'message': f"Failed to set initial version: {str(e)}"
            }
            self.results['errors'].append(str(e))
            return False
            
    def run_initialization(self) -> bool:
        """Run complete database initialization"""
        success = True
        
        # Create database and get engine
        engine = self.create_database()
        if not engine:
            success = False
        else:
            # Create tables
            if not self.create_tables(engine):
                success = False
                
            # Create admin user
            if not self.create_admin_user(engine):
                success = False
                
            # Set initial version
            if not self.set_initial_version(engine):
                success = False
                
        # Save results
        results_file = self.workspace_root / '.testing' / 'database_init_results.json'
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
            
        if success:
            logging.info("Database initialization completed successfully")
        else:
            logging.error("Database initialization failed")
            
        return success

if __name__ == '__main__':
    initializer = DatabaseInitializer()
    success = initializer.run_initialization()
    sys.exit(0 if success else 1) 