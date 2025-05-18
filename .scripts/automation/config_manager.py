"""
Secure configuration manager for handling sensitive configuration files.
"""
import os
import json
import yaml
import base64
from pathlib import Path
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class ConfigManager:
    def __init__(self, config_dir: str = ".config"):
        self.config_dir = Path(config_dir)
        self.env_dir = self.config_dir / "environment"
        self.key_file = self.config_dir / ".key"
        self.salt_file = self.config_dir / ".salt"
        self.environments = ["development", "testing", "production"]
        
        # Ensure config directories exist
        self.config_dir.mkdir(exist_ok=True)
        self.env_dir.mkdir(exist_ok=True)
        for env in self.environments:
            (self.env_dir / env).mkdir(exist_ok=True)
            
        # Initialize encryption
        self._initialize_encryption()
        
    def _initialize_encryption(self):
        """Initialize encryption key and salt"""
        if not self.salt_file.exists():
            salt = os.urandom(16)
            with open(self.salt_file, 'wb') as f:
                f.write(salt)
        else:
            with open(self.salt_file, 'rb') as f:
                salt = f.read()
                
        if not self.key_file.exists():
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
        else:
            with open(self.key_file, 'rb') as f:
                key = f.read()
                
        self.fernet = Fernet(key)
        
    def _encrypt_value(self, value: str) -> bytes:
        """Encrypt a string value"""
        return self.fernet.encrypt(value.encode())
        
    def _decrypt_value(self, encrypted: bytes) -> str:
        """Decrypt an encrypted value"""
        return self.fernet.decrypt(encrypted).decode()
        
    def _secure_file_permissions(self, file_path: Path):
        """Set secure file permissions"""
        # Set file to read/write for owner only
        os.chmod(file_path, 0o600)
        
    def save_config(self, config: Dict[str, Any], environment: str):
        """Save configuration securely"""
        if environment not in self.environments:
            raise ValueError(f"Invalid environment: {environment}")
            
        # Encrypt sensitive values
        encrypted_config = {}
        for key, value in config.items():
            if isinstance(value, str) and any(
                sensitive in key.lower() 
                for sensitive in ['password', 'secret', 'key', 'token']
            ):
                encrypted_config[key] = self._encrypt_value(value).decode()
            else:
                encrypted_config[key] = value
                
        # Save to file
        config_file = self.env_dir / environment / "config.json"
        with open(config_file, 'w') as f:
            json.dump(encrypted_config, f, indent=2)
            
        # Set secure permissions
        self._secure_file_permissions(config_file)
        
    def load_config(self, environment: str) -> Dict[str, Any]:
        """Load configuration securely"""
        if environment not in self.environments:
            raise ValueError(f"Invalid environment: {environment}")
            
        config_file = self.env_dir / environment / "config.json"
        if not config_file.exists():
            return {}
            
        with open(config_file, 'r') as f:
            encrypted_config = json.load(f)
            
        # Decrypt sensitive values
        config = {}
        for key, value in encrypted_config.items():
            if isinstance(value, str) and any(
                sensitive in key.lower() 
                for sensitive in ['password', 'secret', 'key', 'token']
            ):
                try:
                    config[key] = self._decrypt_value(value.encode())
                except Exception:
                    # If decryption fails, assume it's not an encrypted value
                    config[key] = value
            else:
                config[key] = value
                
        return config
        
    def update_config(self, updates: Dict[str, Any], environment: str):
        """Update configuration securely"""
        current_config = self.load_config(environment)
        current_config.update(updates)
        self.save_config(current_config, environment)
        
    def delete_config(self, environment: str):
        """Delete configuration securely"""
        if environment not in self.environments:
            raise ValueError(f"Invalid environment: {environment}")
            
        config_file = self.env_dir / environment / "config.json"
        if config_file.exists():
            config_file.unlink()
            
    def secure_all_configs(self):
        """Secure all configuration files"""
        # Secure config directory
        self._secure_file_permissions(self.config_dir)
        self._secure_file_permissions(self.env_dir)
        
        # Secure environment directories and files
        for env in self.environments:
            env_dir = self.env_dir / env
            self._secure_file_permissions(env_dir)
            
            config_file = env_dir / "config.json"
            if config_file.exists():
                self._secure_file_permissions(config_file)
                
        # Secure encryption files
        self._secure_file_permissions(self.key_file)
        self._secure_file_permissions(self.salt_file)
        
    def migrate_legacy_configs(self):
        """Migrate legacy configuration files to secure format"""
        legacy_paths = [
            ".backup/backup_config.json",
            ".deployment/deployment_config.json",
            ".health/health_config.json",
            ".cursor/config.json"
        ]
        
        for path in legacy_paths:
            legacy_file = Path(path)
            if legacy_file.exists():
                try:
                    # Read legacy config
                    with open(legacy_file, 'r') as f:
                        config = json.load(f)
                        
                    # Save to secure location
                    self.save_config(config, "development")
                    
                    # Delete legacy file
                    legacy_file.unlink()
                    
                    print(f"Migrated {path} to secure configuration")
                except Exception as e:
                    print(f"Error migrating {path}: {e}")
                    
if __name__ == "__main__":
    # Initialize config manager
    config_manager = ConfigManager()
    
    # Secure all configurations
    config_manager.secure_all_configs()
    
    # Migrate legacy configs
    config_manager.migrate_legacy_configs()
    
    print("Configuration security hardening complete") 