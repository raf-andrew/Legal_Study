#!/usr/bin/env python3
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
import json
from typing import Dict, Any, List
import sqlalchemy as sa
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.testing/database_verification.log'),
        logging.StreamHandler()
    ]
)

class DatabaseVerifier:
    def __init__(self):
        self.workspace_root = Path(__file__).parent
        self.env_file = self.workspace_root / 'env.dev'
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'errors': []
        }
        self.db_url = self._get_database_url()
        
    def _get_database_url(self) -> str:
        """Get database URL from environment file"""
        if not self.env_file.exists():
            raise FileNotFoundError(f"Environment file not found: {self.env_file}")
            
        with open(self.env_file) as f:
            for line in f:
                if line.startswith('DATABASE_URL='):
                    return line.split('=', 1)[1].strip().strip('"\'')
        
        raise ValueError("DATABASE_URL not found in environment file")
    
    def verify_database_connection(self) -> bool:
        """Verify database connection"""
        try:
            engine = create_engine(self.db_url)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1")).scalar()
                self.results['checks']['database_connection'] = {
                    'status': 'pass' if result == 1 else 'fail',
                    'details': 'Database connection successful' if result == 1 else 'Database connection failed'
                }
                return result == 1
        except SQLAlchemyError as e:
            self.results['checks']['database_connection'] = {
                'status': 'fail',
                'details': str(e)
            }
            self.results['errors'].append(f'Database connection error: {str(e)}')
            return False
    
    def verify_tables(self, expected_tables: List[str]) -> bool:
        """Verify that all expected tables exist"""
        try:
            engine = create_engine(self.db_url)
            inspector = sa.inspect(engine)
            existing_tables = inspector.get_table_names()
            
            missing_tables = [table for table in expected_tables if table not in existing_tables]
            
            if missing_tables:
                self.results['checks']['tables'] = {
                    'status': 'fail',
                    'details': f'Missing tables: {", ".join(missing_tables)}'
                }
                self.results['errors'].append(f'Missing tables: {", ".join(missing_tables)}')
                return False
            
            self.results['checks']['tables'] = {
                'status': 'pass',
                'details': 'All expected tables exist'
            }
            return True
            
        except SQLAlchemyError as e:
            self.results['checks']['tables'] = {
                'status': 'fail',
                'details': str(e)
            }
            self.results['errors'].append(f'Error checking tables: {str(e)}')
            return False
    
    def verify_migrations(self) -> bool:
        """Verify migration history table exists and has entries"""
        try:
            engine = create_engine(self.db_url)
            inspector = sa.inspect(engine)
            
            if 'alembic_version' not in inspector.get_table_names():
                self.results['checks']['migrations'] = {
                    'status': 'fail',
                    'details': 'Alembic version table not found'
                }
                self.results['errors'].append('Migration history table not found')
                return False
            
            with engine.connect() as conn:
                version = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
                if not version:
                    self.results['checks']['migrations'] = {
                        'status': 'fail',
                        'details': 'No migration version found'
                    }
                    self.results['errors'].append('No migration version found')
                    return False
                
                self.results['checks']['migrations'] = {
                    'status': 'pass',
                    'details': f'Current migration version: {version}'
                }
                return True
                
        except SQLAlchemyError as e:
            self.results['checks']['migrations'] = {
                'status': 'fail',
                'details': str(e)
            }
            self.results['errors'].append(f'Error checking migrations: {str(e)}')
            return False
    
    def verify_seed_data(self, table_counts: Dict[str, int]) -> bool:
        """Verify that tables have the expected number of rows"""
        try:
            engine = create_engine(self.db_url)
            all_correct = True
            
            for table, expected_count in table_counts.items():
                try:
                    with engine.connect() as conn:
                        actual_count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                        
                        if actual_count != expected_count:
                            self.results['checks'][f'seed_data_{table}'] = {
                                'status': 'fail',
                                'details': f'Expected {expected_count} rows, found {actual_count}'
                            }
                            self.results['errors'].append(
                                f'Incorrect row count in {table}: expected {expected_count}, found {actual_count}'
                            )
                            all_correct = False
                        else:
                            self.results['checks'][f'seed_data_{table}'] = {
                                'status': 'pass',
                                'details': f'Found expected {expected_count} rows'
                            }
                except SQLAlchemyError as e:
                    self.results['checks'][f'seed_data_{table}'] = {
                        'status': 'fail',
                        'details': str(e)
                    }
                    self.results['errors'].append(f'Error checking seed data for {table}: {str(e)}')
                    all_correct = False
            
            return all_correct
            
        except SQLAlchemyError as e:
            self.results['checks']['seed_data'] = {
                'status': 'fail',
                'details': str(e)
            }
            self.results['errors'].append(f'Error checking seed data: {str(e)}')
            return False
    
    def run_verification(self, expected_tables: List[str], table_counts: Dict[str, int]) -> bool:
        """Run all database verification checks"""
        logging.info("Starting database verification...")
        
        success = True
        success &= self.verify_database_connection()
        success &= self.verify_tables(expected_tables)
        success &= self.verify_migrations()
        success &= self.verify_seed_data(table_counts)
        
        # Save results
        results_file = self.workspace_root / '.testing' / 'database_verification_results.json'
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # Log summary
        total_checks = len(self.results['checks'])
        passed_checks = sum(1 for check in self.results['checks'].values() if check['status'] == 'pass')
        failed_checks = sum(1 for check in self.results['checks'].values() if check['status'] == 'fail')
        
        logging.info(f"Verification complete. Results:")
        logging.info(f"Total checks: {total_checks}")
        logging.info(f"Passed: {passed_checks}")
        logging.info(f"Failed: {failed_checks}")
        
        if self.results['errors']:
            logging.error("Errors found:")
            for error in self.results['errors']:
                logging.error(f"- {error}")
        
        return success

if __name__ == '__main__':
    # Expected tables and their row counts
    expected_tables = [
        'users',
        'documents',
        'comments',
        'tags',
        'document_tags'
    ]
    
    table_counts = {
        'users': 1,  # At least admin user
        'documents': 0,
        'comments': 0,
        'tags': 0,
        'document_tags': 0
    }
    
    verifier = DatabaseVerifier()
    success = verifier.run_verification(expected_tables, table_counts)
    sys.exit(0 if success else 1) 