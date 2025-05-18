"""
Bootstrap script for chaos testing framework.
"""
import os
import sys
from pathlib import Path
from deployment_config import DeploymentConfig
from security_config import SecurityConfig

def main():
    """Main bootstrap function."""
    print("Starting chaos test framework bootstrap...")
    
    # Initialize configurations
    deployment_config = DeploymentConfig()
    security_config = SecurityConfig()
    
    # Validate security settings
    print("\nValidating security configuration...")
    for directory in deployment_config.test_directories + deployment_config.error_directories + deployment_config.script_directories:
        if not security_config.validate_path(directory):
            print(f"Error: Invalid directory path: {directory}")
            return False
            
    # Bootstrap environment
    if not deployment_config.bootstrap():
        print("Error: Bootstrap failed")
        return False
        
    # Get Python path
    python_path = deployment_config.get_python_path()
    if not python_path:
        print("Error: Could not find Python executable")
        return False
        
    # Set environment variables
    env_vars = deployment_config.get_environment_variables()
    for key, value in env_vars.items():
        os.environ[key] = value
        
    print("\nBootstrap completed successfully!")
    print(f"Python executable: {python_path}")
    print("Environment variables set:")
    for key, value in env_vars.items():
        print(f"  {key}={value}")
        
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Fatal error during bootstrap: {str(e)}")
        sys.exit(1) 