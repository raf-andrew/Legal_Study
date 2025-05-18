#!/usr/bin/env python3

import os
import sys
import logging
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
import faker
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.logs/test_data_generator.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class TestDataGenerator:
    def __init__(self):
        self.fake = faker.Faker()
        self.test_data = {
            'users': [],
            'cases': [],
            'documents': [],
            'comments': [],
            'tags': []
        }
        
        # Create necessary directories
        os.makedirs('test_data', exist_ok=True)
        os.makedirs('.logs', exist_ok=True)
    
    def load_config(self):
        """Load test configuration."""
        try:
            config_file = Path('.config/test_config.yaml')
            with open(config_file) as f:
                self.config = yaml.safe_load(f)
            
            logger.info("Loaded test configuration")
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            sys.exit(1)
    
    def generate_users(self, count=10):
        """Generate test users."""
        try:
            roles = ['admin', 'user', 'guest']
            
            for _ in range(count):
                user = {
                    'username': self.fake.user_name(),
                    'email': self.fake.email(),
                    'password': self.fake.password(),
                    'role': random.choice(roles),
                    'created_at': self.fake.date_time_this_year().isoformat(),
                    'last_login': self.fake.date_time_this_month().isoformat()
                }
                self.test_data['users'].append(user)
            
            logger.info(f"Generated {count} test users")
            
        except Exception as e:
            logger.error(f"Error generating users: {e}")
    
    def generate_cases(self, count=20):
        """Generate test cases."""
        try:
            statuses = ['open', 'in_progress', 'closed', 'archived']
            priorities = ['high', 'medium', 'low']
            
            for _ in range(count):
                case = {
                    'title': self.fake.sentence(),
                    'description': self.fake.paragraph(),
                    'status': random.choice(statuses),
                    'priority': random.choice(priorities),
                    'created_at': self.fake.date_time_this_year().isoformat(),
                    'updated_at': self.fake.date_time_this_month().isoformat(),
                    'assigned_to': random.choice(self.test_data['users'])['username'] if self.test_data['users'] else None
                }
                self.test_data['cases'].append(case)
            
            logger.info(f"Generated {count} test cases")
            
        except Exception as e:
            logger.error(f"Error generating cases: {e}")
    
    def generate_documents(self, count=15):
        """Generate test documents."""
        try:
            document_types = ['contract', 'brief', 'motion', 'order', 'pleading']
            
            for _ in range(count):
                document = {
                    'title': self.fake.sentence(),
                    'type': random.choice(document_types),
                    'content': self.fake.paragraphs(nb=3),
                    'created_at': self.fake.date_time_this_year().isoformat(),
                    'updated_at': self.fake.date_time_this_month().isoformat(),
                    'case_id': random.choice(range(1, len(self.test_data['cases']) + 1)) if self.test_data['cases'] else None,
                    'author': random.choice(self.test_data['users'])['username'] if self.test_data['users'] else None
                }
                self.test_data['documents'].append(document)
            
            logger.info(f"Generated {count} test documents")
            
        except Exception as e:
            logger.error(f"Error generating documents: {e}")
    
    def generate_comments(self, count=30):
        """Generate test comments."""
        try:
            for _ in range(count):
                comment = {
                    'content': self.fake.paragraph(),
                    'created_at': self.fake.date_time_this_year().isoformat(),
                    'author': random.choice(self.test_data['users'])['username'] if self.test_data['users'] else None,
                    'case_id': random.choice(range(1, len(self.test_data['cases']) + 1)) if self.test_data['cases'] else None,
                    'document_id': random.choice(range(1, len(self.test_data['documents']) + 1)) if self.test_data['documents'] else None
                }
                self.test_data['comments'].append(comment)
            
            logger.info(f"Generated {count} test comments")
            
        except Exception as e:
            logger.error(f"Error generating comments: {e}")
    
    def generate_tags(self, count=10):
        """Generate test tags."""
        try:
            for _ in range(count):
                tag = {
                    'name': self.fake.word(),
                    'description': self.fake.sentence(),
                    'created_at': self.fake.date_time_this_year().isoformat()
                }
                self.test_data['tags'].append(tag)
            
            logger.info(f"Generated {count} test tags")
            
        except Exception as e:
            logger.error(f"Error generating tags: {e}")
    
    def save_test_data(self):
        """Save generated test data to files."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            for data_type, data in self.test_data.items():
                output_file = Path('test_data') / f'{data_type}_{timestamp}.json'
                with open(output_file, 'w') as f:
                    json.dump(data, f, indent=2)
                
                logger.info(f"Saved {len(data)} {data_type} to {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving test data: {e}")
    
    def generate_data(self):
        """Main data generation process."""
        try:
            logger.info("Starting test data generation")
            
            # Load configuration
            self.load_config()
            
            # Generate data
            self.generate_users()
            self.generate_cases()
            self.generate_documents()
            self.generate_comments()
            self.generate_tags()
            
            # Save data
            self.save_test_data()
            
            logger.info("Test data generation completed")
            
        except Exception as e:
            logger.error(f"Error in data generation process: {e}")
            sys.exit(1)

if __name__ == "__main__":
    generator = TestDataGenerator()
    generator.generate_data() 