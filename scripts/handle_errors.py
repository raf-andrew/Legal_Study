#!/usr/bin/env python3

import os
import sys
import logging
import json
from datetime import datetime
from pathlib import Path
import traceback
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.logs/error_handler.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class ErrorHandler:
    def __init__(self):
        self.errors = []
        self.error_counts = {
            'critical': 0,
            'error': 0,
            'warning': 0
        }
        
        # Create necessary directories
        os.makedirs('.errors', exist_ok=True)
        os.makedirs('.logs', exist_ok=True)
    
    def log_error(self, error_type, message, traceback_info=None):
        """Log an error with details."""
        error = {
            'timestamp': datetime.now().isoformat(),
            'type': error_type,
            'message': message,
            'traceback': traceback_info
        }
        
        self.errors.append(error)
        self.error_counts[error_type] += 1
        
        # Log to file
        error_file = Path('.errors') / f'error_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(error_file, 'w') as f:
            json.dump(error, f, indent=2)
        
        logger.error(f"{error_type.upper()}: {message}")
        if traceback_info:
            logger.error(f"Traceback: {traceback_info}")
    
    def analyze_errors(self):
        """Analyze collected errors."""
        analysis = {
            'total_errors': len(self.errors),
            'error_types': self.error_counts,
            'common_patterns': {},
            'recommendations': []
        }
        
        # Analyze error patterns
        for error in self.errors:
            error_message = error['message']
            if error_message not in analysis['common_patterns']:
                analysis['common_patterns'][error_message] = 0
            analysis['common_patterns'][error_message] += 1
        
        # Generate recommendations
        if self.error_counts['critical'] > 0:
            analysis['recommendations'].append({
                'priority': 'high',
                'action': 'Address critical errors immediately',
                'details': f"Found {self.error_counts['critical']} critical errors"
            })
        
        if self.error_counts['error'] > 5:
            analysis['recommendations'].append({
                'priority': 'medium',
                'action': 'Review and fix recurring errors',
                'details': f"Found {self.error_counts['error']} errors"
            })
        
        if self.error_counts['warning'] > 10:
            analysis['recommendations'].append({
                'priority': 'low',
                'action': 'Clean up warning messages',
                'details': f"Found {self.error_counts['warning']} warnings"
            })
        
        return analysis
    
    def send_error_report(self, analysis):
        """Send error report via email."""
        try:
            # Email configuration
            sender = "test-monitor@example.com"
            receiver = "admin@example.com"
            subject = f"Test Error Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = sender
            msg['To'] = receiver
            msg['Subject'] = subject
            
            # Email body
            body = f"""
            Test Error Report
            =================
            
            Summary:
            - Total Errors: {analysis['total_errors']}
            - Critical Errors: {analysis['error_types']['critical']}
            - Errors: {analysis['error_types']['error']}
            - Warnings: {analysis['error_types']['warning']}
            
            Recommendations:
            {chr(10).join(f"- {rec['action']} ({rec['priority']} priority)" for rec in analysis['recommendations'])}
            
            For detailed information, please check the error logs in the .errors directory.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP('localhost') as server:
                server.send_message(msg)
            
            logger.info("Error report sent successfully")
            
        except Exception as e:
            logger.error(f"Error sending report: {e}")
    
    def save_analysis(self, analysis):
        """Save error analysis to file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            analysis_file = Path('.errors') / f'error_analysis_{timestamp}.json'
            
            with open(analysis_file, 'w') as f:
                json.dump(analysis, f, indent=2)
            
            logger.info(f"Error analysis saved to {analysis_file}")
            
        except Exception as e:
            logger.error(f"Error saving analysis: {e}")
    
    def handle_errors(self):
        """Main error handling process."""
        try:
            # Collect errors from test execution
            # Add your error collection code here
            
            # Analyze errors
            analysis = self.analyze_errors()
            
            # Save analysis
            self.save_analysis(analysis)
            
            # Send report if there are errors
            if self.errors:
                self.send_error_report(analysis)
            
            logger.info("Error handling completed")
            
        except Exception as e:
            logger.error(f"Error in error handling process: {e}")
            sys.exit(1)

if __name__ == "__main__":
    handler = ErrorHandler()
    handler.handle_errors() 