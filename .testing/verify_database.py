#!/usr/bin/env python3
import os
import sys
import json
from pathlib import Path
import logging
from datetime import datetime
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.testing/database_verification.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class DatabaseVerifier:
    def __init__(self):
        self.workspace_root = Path(__file__).parent.parent
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'errors': []
        }
        self.expected_tables = {
            'users': {'min_rows': 1},  # At least one admin user
            'documents': {'min_rows': 0},
            'comments': {'min_rows': 0},
            'tags': {'min_rows': 0},
            'document_tags': {'min_rows': 0},
            'alembic_version': {'min_rows': 1}  # Should have current migration version
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
            
    def verify_database_connection(self) -> bool:
        """Verify database connection"""
        try:
            database_url = self._get_database_url()
            engine = create_engine(database_url)
            
            # Test connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                
            self.results['checks']['database_connection'] = {
                'status': 'pass',
                'message': "Successfully connected to database"
            }
            return engine
            
        except Exception as e:
            self.results['checks']['database_connection'] = {
                'status': 'fail',
                'message': f"Failed to connect to database: {str(e)}"
            }
            self.results['errors'].append(str(e))
            return None
            
    def verify_tables(self, engine) -> bool:
        """Verify all expected tables exist"""
        try:
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()
            
            missing_tables = set(self.expected_tables.keys()) - set(existing_tables)
            if missing_tables:
                self.results['checks']['tables_exist'] = {
                    'status': 'fail',
                    'message': f"Missing tables: {', '.join(missing_tables)}"
                }
                return False
                
            self.results['checks']['tables_exist'] = {
                'status': 'pass',
                'message': "All expected tables exist"
            }
            return True
            
        except Exception as e:
            self.results['checks']['tables_exist'] = {
                'status': 'fail',
                'message': f"Failed to verify tables: {str(e)}"
            }
            self.results['errors'].append(str(e))
            return False
            
    def verify_row_counts(self, engine) -> bool:
        """Verify minimum row counts for tables"""
        try:
            success = True
            with engine.connect() as conn:
                for table, config in self.expected_tables.items():
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    
                    if count < config['min_rows']:
                        self.results['checks'][f'row_count_{table}'] = {
                            'status': 'fail',
                            'message': f"Table {table} has {count} rows, expected at least {config['min_rows']}"
                        }
                        success = False
                    else:
                        self.results['checks'][f'row_count_{table}'] = {
                            'status': 'pass',
                            'message': f"Table {table} has sufficient rows ({count})"
                        }
                        
            return success
            
        except Exception as e:
            self.results['checks']['row_counts'] = {
                'status': 'fail',
                'message': f"Failed to verify row counts: {str(e)}"
            }
            self.results['errors'].append(str(e))
            return False
            
    def verify_migrations(self, engine) -> bool:
        """Verify migration status"""
        try:
            with engine.connect() as conn:
                # Check alembic_version table exists and has exactly one row
                result = conn.execute(text("SELECT COUNT(*) FROM alembic_version"))
                count = result.scalar()
                
                if count != 1:
                    self.results['checks']['migration_version'] = {
                        'status': 'fail',
                        'message': f"Expected exactly 1 row in alembic_version, found {count}"
                    }
                    return False
                    
                # Get current version
                result = conn.execute(text("SELECT version_num FROM alembic_version"))
                version = result.scalar()
                
                self.results['checks']['migration_version'] = {
                    'status': 'pass',
                    'message': f"Database is at migration version: {version}"
                }
                return True
                
        except Exception as e:
            self.results['checks']['migration_version'] = {
                'status': 'fail',
                'message': f"Failed to verify migrations: {str(e)}"
            }
            self.results['errors'].append(str(e))
            return False
            
    def run_verification(self) -> bool:
        """Run all verification checks"""
        success = True
        
        # First verify database connection
        engine = self.verify_database_connection()
        if not engine:
            success = False
        else:
            # Only continue with other checks if connection succeeds
            if not self.verify_tables(engine):
                success = False
                
            if not self.verify_row_counts(engine):
                success = False
                
            if not self.verify_migrations(engine):
                success = False
                
        # Save results
        results_file = self.workspace_root / '.testing' / 'database_verification_results.json'
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
            
        if success:
            logging.info("All database checks passed")
        else:
            logging.error("Some database checks failed")
            
        return success

if __name__ == '__main__':
    verifier = DatabaseVerifier()
    success = verifier.run_verification()
    sys.exit(0 if success else 1) 