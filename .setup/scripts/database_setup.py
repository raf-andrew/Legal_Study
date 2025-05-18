#!/usr/bin/env python3

import os
import sys
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any
import psycopg2
import mysql.connector
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

def setup_postgresql(config: Dict[str, Any]) -> bool:
    """Setup PostgreSQL database."""
    try:
        # Extract database configuration
        db_config = config['database']
        host = db_config['host']
        port = db_config['port']
        dbname = db_config['name']
        user = db_config['user']
        password = db_config['password']

        # Create database if it doesn't exist
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
        exists = cursor.fetchone()

        if not exists:
            cursor.execute(f"CREATE DATABASE {dbname}")
            logger.info(f"Created database {dbname}")

        cursor.close()
        conn.close()

        # Create SQLAlchemy engine
        engine = create_engine(
            f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
        )

        # Create tables
        from legal_study.models import Base
        Base.metadata.create_all(engine)

        logger.info("PostgreSQL setup completed successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to setup PostgreSQL: {str(e)}")
        return False

def setup_mysql(config: Dict[str, Any]) -> bool:
    """Setup MySQL database."""
    try:
        # Extract database configuration
        db_config = config['database']
        host = db_config['host']
        port = db_config['port']
        dbname = db_config['name']
        user = db_config['user']
        password = db_config['password']

        # Create database if it doesn't exist
        conn = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password
        )
        cursor = conn.cursor()

        # Check if database exists
        cursor.execute(f"SHOW DATABASES LIKE '{dbname}'")
        exists = cursor.fetchone()

        if not exists:
            cursor.execute(f"CREATE DATABASE {dbname}")
            logger.info(f"Created database {dbname}")

        cursor.close()
        conn.close()

        # Create SQLAlchemy engine
        engine = create_engine(
            f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{dbname}"
        )

        # Create tables
        from legal_study.models import Base
        Base.metadata.create_all(engine)

        logger.info("MySQL setup completed successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to setup MySQL: {str(e)}")
        return False

def setup_database(config: Dict[str, Any]) -> bool:
    """Main database setup function."""
    db_type = config['database']['type'].lower()

    setup_functions = {
        'postgresql': setup_postgresql,
        'mysql': setup_mysql
    }

    setup_function = setup_functions.get(db_type)
    if not setup_function:
        logger.error(f"Unsupported database type: {db_type}")
        return False

    return setup_function(config)

def run_migrations(config: Dict[str, Any]) -> bool:
    """Run database migrations."""
    try:
        # Extract database configuration
        db_config = config['database']
        db_type = db_config['type'].lower()

        # Run migrations based on database type
        if db_type == 'postgresql':
            subprocess.run(['alembic', 'upgrade', 'head'], check=True)
        elif db_type == 'mysql':
            subprocess.run(['alembic', 'upgrade', 'head'], check=True)

        logger.info("Database migrations completed successfully")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to run migrations: {str(e)}")
        return False

if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Test configuration
    test_config = {
        'database': {
            'type': 'postgresql',
            'host': 'localhost',
            'port': '5432',
            'name': 'legal_study',
            'user': 'postgres',
            'password': 'postgres'
        }
    }

    success = setup_database(test_config)
    if success:
        success = run_migrations(test_config)

    sys.exit(0 if success else 1)
