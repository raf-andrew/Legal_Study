"""
Permissions manager for handling file and directory permissions.
"""
import os
import stat
import logging
from pathlib import Path
from typing import List, Set

class PermissionsManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Define restricted file patterns
        self.restricted_files = {
            '*.key', '*.pem', '*.cert', '*.env',
            'config.json', 'secrets.json', 'credentials.json'
        }
        
        # Define directories that need special handling
        self.script_dirs = {'.scripts', 'tests', 'tools'}
        self.config_dirs = {'config', 'settings'}
        self.data_dirs = {'data', 'logs', 'output'}
        
        # Virtual environment directories that should be excluded from strict permissions
        self.venv_exclude_dirs = {
            '.venv/Lib/site-packages',
            '.venv/Scripts',
            '.venv/pyvenv.cfg'
        }

    def secure_directory(self, dir_path: str, exclude_patterns: Set[str] = None) -> None:
        """Secure a directory by setting appropriate permissions."""
        if exclude_patterns and any(pattern in dir_path for pattern in exclude_patterns):
            return
            
        try:
            # Set directory permissions to rwx for owner only (700)
            os.chmod(dir_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
            self.logger.info(f"Secured directory: {dir_path}")
        except Exception as e:
            self.logger.error(f"Failed to secure directory {dir_path}: {str(e)}")

    def secure_file(self, file_path: str, is_script: bool = False) -> None:
        """Secure a file by setting appropriate permissions."""
        try:
            if is_script:
                # Set script file permissions to rwx for owner only (700)
                os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
            else:
                # Set regular file permissions to rw for owner only (600)
                os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR)
            self.logger.info(f"Secured file: {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to secure file {file_path}: {str(e)}")

    def is_script_file(self, file_path: str) -> bool:
        """Check if a file is a script that needs execute permissions."""
        return (file_path.endswith('.py') or 
                file_path.endswith('.sh') or 
                file_path.endswith('.exe') or
                file_path.endswith('.bat') or
                file_path.endswith('.ps1'))

    def secure_workspace(self, workspace_root: str = '.') -> None:
        """Secure the entire workspace recursively."""
        for root, dirs, files in os.walk(workspace_root):
            # Skip excluded virtual environment directories
            if any(venv_dir in root for venv_dir in self.venv_exclude_dirs):
                continue
                
            # Secure the current directory
            self.secure_directory(root, self.venv_exclude_dirs)
            
            # Secure all files in the directory
            for file in files:
                file_path = os.path.join(root, file)
                is_script = self.is_script_file(file_path)
                self.secure_file(file_path, is_script)

    def audit_permissions(self, workspace_root: str = '.') -> List[str]:
        """Audit workspace permissions and return a list of issues found."""
        issues = []
        
        for root, dirs, files in os.walk(workspace_root):
            # Skip excluded virtual environment directories
            if any(venv_dir in root for venv_dir in self.venv_exclude_dirs):
                continue
                
            # Check directory permissions
            dir_stat = os.stat(root)
            if dir_stat.st_mode & stat.S_IRWXO or dir_stat.st_mode & stat.S_IRWXG:
                issues.append(f"Directory permissions too permissive: {root}")
            
            # Check file permissions
            for file in files:
                file_path = os.path.join(root, file)
                file_stat = os.stat(file_path)
                
                if file_stat.st_mode & stat.S_IRWXO or file_stat.st_mode & stat.S_IRWXG:
                    issues.append(f"File permissions too permissive: {file_path}")
        
        return issues

def main():
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run the permissions manager
    pm = PermissionsManager()
    
    # Audit current permissions
    logging.info("Auditing current permissions...")
    issues = pm.audit_permissions()
    if issues:
        logging.warning("Found permission issues:")
        for issue in issues:
            logging.warning(f"- {issue}")
    
    # Secure the workspace
    logging.info("Securing workspace...")
    pm.secure_workspace()
    
    # Verify permissions after securing
    logging.info("Verifying permissions...")
    remaining_issues = pm.audit_permissions()
    if remaining_issues:
        logging.warning("Remaining permission issues:")
        for issue in remaining_issues:
            logging.warning(f"- {issue}")
    else:
        logging.info("All permissions secured successfully!")

if __name__ == '__main__':
    main() 