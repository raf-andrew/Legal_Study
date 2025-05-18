#!/usr/bin/env python3
"""
Unit Tests for Health Check Command
"""

import unittest
import os
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add the controls directory to the Python path
sys.path.append(str(Path(__file__).parent.parent / '.controls' / 'commands' / 'health'))

from check import HealthCheck

class TestHealthCheck(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.health_check = HealthCheck()
        self.test_root = Path(__file__).parent.parent
        self.health_check.root_dir = self.test_root

    def test_check_directory_structure(self):
        """Test directory structure check"""
        # Create test directories
        test_dirs = [
            '.controls',
            '.security',
            '.chaos',
            '.ui',
            '.ux',
            '.refactoring',
            '.guide',
            '.api',
            '.integration',
            '.unit',
            '.sniff',
            '.test',
            '.completed',
            '.errors',
            '.qa'
        ]
        
        for dir_name in test_dirs:
            dir_path = self.test_root / dir_name
            dir_path.mkdir(exist_ok=True)
            
        # Run directory check
        self.health_check._check_directory_structure()
        
        # Verify no errors
        self.assertEqual(len(self.health_check.results['errors']), 0)
        
        # Clean up
        for dir_name in test_dirs:
            dir_path = self.test_root / dir_name
            dir_path.rmdir()

    def test_check_configuration(self):
        """Test configuration check"""
        # Create test config files
        config_files = [
            '.config/environment/development/config.json',
            '.config/environment/testing/config.json',
            '.config/environment/production/config.json'
        ]
        
        for config_file in config_files:
            file_path = self.test_root / config_file
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w') as f:
                json.dump({}, f)
                
        # Run configuration check
        self.health_check._check_configuration()
        
        # Verify no errors
        self.assertEqual(len(self.health_check.results['errors']), 0)
        
        # Clean up
        for config_file in config_files:
            file_path = self.test_root / config_file
            file_path.unlink()
            file_path.parent.rmdir()

    @patch('subprocess.run')
    def test_check_services(self, mock_run):
        """Test services check"""
        # Mock service checks
        mock_run.return_value = MagicMock(returncode=0)
        
        # Run services check
        self.health_check._check_services()
        
        # Verify no errors
        self.assertEqual(len(self.health_check.results['errors']), 0)

    def test_check_security(self):
        """Test security check"""
        # Run security check
        self.health_check._check_security()
        
        # Verify no errors
        self.assertEqual(len(self.health_check.results['errors']), 0)

    def test_check_monitoring(self):
        """Test monitoring check"""
        # Run monitoring check
        self.health_check._check_monitoring()
        
        # Verify no errors
        self.assertEqual(len(self.health_check.results['errors']), 0)

    def test_generate_report(self):
        """Test report generation"""
        # Set up test data
        self.health_check.results = {
            'timestamp': datetime.now().isoformat(),
            'checks': {
                'directory': 'passed',
                'configuration': 'passed',
                'services': 'passed',
                'security': 'passed',
                'monitoring': 'passed'
            },
            'status': 'healthy',
            'errors': []
        }
        
        # Generate report
        report = self.health_check.generate_report()
        
        # Verify report format
        self.assertIsInstance(report, str)
        report_data = json.loads(report)
        self.assertIn('timestamp', report_data)
        self.assertIn('checks', report_data)
        self.assertIn('status', report_data)
        self.assertIn('errors', report_data)

    def test_check_system_health(self):
        """Test complete system health check"""
        # Mock all check methods
        with patch.object(HealthCheck, '_check_directory_structure') as mock_dir, \
             patch.object(HealthCheck, '_check_configuration') as mock_config, \
             patch.object(HealthCheck, '_check_services') as mock_services, \
             patch.object(HealthCheck, '_check_security') as mock_security, \
             patch.object(HealthCheck, '_check_monitoring') as mock_monitoring:
            
            # Set up mocks
            mock_dir.return_value = None
            mock_config.return_value = None
            mock_services.return_value = None
            mock_security.return_value = None
            mock_monitoring.return_value = None
            
            # Run health check
            result = self.health_check.check_system_health()
            
            # Verify result
            self.assertTrue(result)
            self.assertEqual(self.health_check.results['status'], 'healthy')

if __name__ == '__main__':
    unittest.main() 