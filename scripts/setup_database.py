"""
Script to set up database for sniffing infrastructure.
"""
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger("setup_database")

def main() -> int:
    """Main entry point for database setup."""
    try:
        # Set up logging
        setup_logging()

        # Load configuration
        config = load_config()
        if not config:
            logger.error("Failed to load configuration")
            return 1

        # Set up database
        if not setup_database(config):
            logger.error("Failed to set up database")
            return 1

        logger.info("Database set up successfully")
        return 0

    except Exception as e:
        logger.error(f"Error setting up database: {e}")
        return 1

def setup_logging() -> None:
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

def load_config() -> Optional[Dict[str, Any]]:
    """Load sniffing configuration."""
    try:
        config_path = Path("sniffing/config/sniffing_config.yaml")
        if not config_path.exists():
            logger.error(f"Configuration file not found: {config_path}")
            return None

        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        return config

    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return None

def setup_database(config: Dict[str, Any]) -> bool:
    """Set up database."""
    try:
        # Get database configuration
        db_config = config.get("database", {})
        if not db_config:
            logger.error("No database configuration found")
            return False

        # Create database URL
        db_url = create_database_url(db_config)
        if not db_url:
            return False

        # Create database
        if not create_database(db_url, db_config):
            return False

        # Create tables
        if not create_tables(db_url):
            return False

        # Create indexes
        if not create_indexes(db_url):
            return False

        # Set up migrations
        if not setup_migrations(db_config):
            return False

        return True

    except Exception as e:
        logger.error(f"Error setting up database: {e}")
        return False

def create_database_url(config: Dict[str, Any]) -> Optional[str]:
    """Create database URL."""
    try:
        # Get database parameters
        db_type = config.get("type", "postgresql")
        db_host = config.get("host", "localhost")
        db_port = config.get("port", 5432)
        db_name = config.get("name", "sniffing")
        db_user = config.get("user", "")
        db_password = config.get("password", "")

        # Create URL
        if db_type == "postgresql":
            return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        elif db_type == "mysql":
            return f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        elif db_type == "sqlite":
            return f"sqlite:///{db_name}.db"
        else:
            logger.error(f"Unsupported database type: {db_type}")
            return None

    except Exception as e:
        logger.error(f"Error creating database URL: {e}")
        return None

def create_database(url: str, config: Dict[str, Any]) -> bool:
    """Create database."""
    try:
        # Create engine
        engine = create_engine(url)

        # Create database
        with engine.connect() as conn:
            conn.execute(text("CREATE DATABASE IF NOT EXISTS sniffing"))

        logger.info("Database created")
        return True

    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        return False

def create_tables(url: str) -> bool:
    """Create database tables."""
    try:
        # Create engine
        engine = create_engine(url)

        # Create tables
        tables = [
            """
            CREATE TABLE IF NOT EXISTS sniffing_results (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                domain VARCHAR(50) NOT NULL,
                file_path TEXT NOT NULL,
                status VARCHAR(20) NOT NULL,
                issues JSONB,
                metrics JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS issues (
                id SERIAL PRIMARY KEY,
                result_id INTEGER REFERENCES sniffing_results(id),
                type VARCHAR(50) NOT NULL,
                severity VARCHAR(20) NOT NULL,
                description TEXT NOT NULL,
                location JSONB,
                fixed BOOLEAN DEFAULT FALSE,
                fixed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS metrics (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                domain VARCHAR(50) NOT NULL,
                name VARCHAR(100) NOT NULL,
                value FLOAT NOT NULL,
                labels JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS reports (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                type VARCHAR(50) NOT NULL,
                content JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]

        # Execute table creation
        with engine.connect() as conn:
            for table in tables:
                conn.execute(text(table))
                conn.commit()

        logger.info("Tables created")
        return True

    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        return False

def create_indexes(url: str) -> bool:
    """Create database indexes."""
    try:
        # Create engine
        engine = create_engine(url)

        # Create indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_results_timestamp ON sniffing_results(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_results_domain ON sniffing_results(domain)",
            "CREATE INDEX IF NOT EXISTS idx_results_status ON sniffing_results(status)",
            "CREATE INDEX IF NOT EXISTS idx_issues_type ON issues(type)",
            "CREATE INDEX IF NOT EXISTS idx_issues_severity ON issues(severity)",
            "CREATE INDEX IF NOT EXISTS idx_issues_fixed ON issues(fixed)",
            "CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_metrics_domain ON metrics(domain)",
            "CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(name)",
            "CREATE INDEX IF NOT EXISTS idx_reports_timestamp ON reports(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_reports_type ON reports(type)"
        ]

        # Execute index creation
        with engine.connect() as conn:
            for index in indexes:
                conn.execute(text(index))
                conn.commit()

        logger.info("Indexes created")
        return True

    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")
        return False

def setup_migrations(config: Dict[str, Any]) -> bool:
    """Set up database migrations."""
    try:
        # Create migrations directory
        migrations_dir = Path("database/migrations")
        migrations_dir.mkdir(parents=True, exist_ok=True)

        # Create initial migration
        migration_path = migrations_dir / "001_initial.sql"
        if not migration_path.exists():
            migration_content = """-- Initial migration

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "hstore";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS sniffing;

-- Set search path
SET search_path TO sniffing,public;

-- Create types
CREATE TYPE severity_level AS ENUM ('low', 'medium', 'high');
CREATE TYPE issue_status AS ENUM ('open', 'fixed', 'wontfix');
CREATE TYPE report_type AS ENUM ('daily', 'weekly', 'monthly');

-- Create functions
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers
CREATE TRIGGER update_sniffing_results_timestamp
    BEFORE UPDATE ON sniffing_results
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_issues_timestamp
    BEFORE UPDATE ON issues
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_metrics_timestamp
    BEFORE UPDATE ON metrics
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_reports_timestamp
    BEFORE UPDATE ON reports
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();
"""
            migration_path.write_text(migration_content)

        # Create migration tracking table
        engine = create_engine(create_database_url(config))
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS migrations (
                    id SERIAL PRIMARY KEY,
                    version VARCHAR(50) NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()

        logger.info("Migrations set up")
        return True

    except Exception as e:
        logger.error(f"Error setting up migrations: {e}")
        return False

def verify_database(url: str) -> bool:
    """Verify database setup."""
    try:
        # Create engine
        engine = create_engine(url)

        # Check connection
        with engine.connect() as conn:
            # Check tables
            tables = [
                "sniffing_results",
                "issues",
                "metrics",
                "reports",
                "migrations"
            ]

            for table in tables:
                result = conn.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = '{table}'
                    )
                """))
                if not result.scalar():
                    logger.error(f"Table not found: {table}")
                    return False

            # Check indexes
            indexes = [
                "idx_results_timestamp",
                "idx_results_domain",
                "idx_results_status",
                "idx_issues_type",
                "idx_issues_severity",
                "idx_issues_fixed",
                "idx_metrics_timestamp",
                "idx_metrics_domain",
                "idx_metrics_name",
                "idx_reports_timestamp",
                "idx_reports_type"
            ]

            for index in indexes:
                result = conn.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM pg_indexes
                        WHERE indexname = '{index}'
                    )
                """))
                if not result.scalar():
                    logger.error(f"Index not found: {index}")
                    return False

        logger.info("Database verification passed")
        return True

    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error verifying database: {e}")
        return False

def cleanup_database(url: str) -> bool:
    """Clean up database."""
    try:
        # Create engine
        engine = create_engine(url)

        # Clean up old data
        with engine.connect() as conn:
            # Delete old results
            conn.execute(text("""
                DELETE FROM sniffing_results
                WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '30 days'
            """))

            # Delete old metrics
            conn.execute(text("""
                DELETE FROM metrics
                WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '30 days'
            """))

            # Delete old reports
            conn.execute(text("""
                DELETE FROM reports
                WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '30 days'
            """))

            conn.commit()

        logger.info("Database cleaned up")
        return True

    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error cleaning up database: {e}")
        return False

if __name__ == "__main__":
    sys.exit(main())
