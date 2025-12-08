"""Secure credential management for testing and operations."""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

# Make dotenv optional - only required for credential-based testing
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    # No-op function if dotenv not available
    def load_dotenv(*args, **kwargs):
        pass


class CredentialManager:
    """Manage credentials from .env and YAML config files.
    
    Supports loading credentials from:
    - Environment variables directly
    - .env files
    - YAML configuration files with environment variable substitution
    """
    
    def __init__(self, env_file: Optional[Path] = None, 
                 config_file: Optional[Path] = None):
        """Initialize credential manager.
        
        Args:
            env_file: Path to .env file (optional, defaults to .env in root)
            config_file: Path to YAML config file (optional)
        """
        # Load .env file
        if env_file and env_file.exists():
            load_dotenv(env_file)
        else:
            load_dotenv()  # Load from default .env if it exists
        
        # Load YAML config if provided
        self.config = {}
        if config_file and config_file.exists():
            self.config = self._load_yaml_config(config_file)
    
    def _load_yaml_config(self, config_file: Path) -> Dict[str, Any]:
        """Load YAML config and substitute environment variables."""
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Recursively substitute ${VAR} with environment variables
        return self._substitute_env_vars(config)
    
    def _substitute_env_vars(self, obj: Any) -> Any:
        """Recursively substitute ${VAR} patterns with environment variables."""
        if isinstance(obj, dict):
            return {k: self._substitute_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._substitute_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            # Replace ${VAR} with environment variable value
            if obj.startswith("${") and obj.endswith("}"):
                var_name = obj[2:-1]
                return os.getenv(var_name, obj)
            return obj
        return obj
    
    def _get_credential(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get credential from environment or config.
        
        Args:
            key: Credential key name
            default: Default value if not found
            
        Returns:
            Credential value or default
        """
        # Try environment variable first
        value = os.getenv(key)
        if value:
            return value
        
        # Try config file
        if self.config:
            # Support nested keys like "zenodo.token"
            parts = key.lower().split('.')
            current = self.config
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return default
            return current if isinstance(current, str) else default
        
        return default
    
    def get_zenodo_credentials(self, use_sandbox: bool = True) -> Dict[str, str]:
        """Get Zenodo API credentials.
        
        Args:
            use_sandbox: Whether to use sandbox environment (default: True)
            
        Returns:
            Dictionary with token and environment info
        """
        token_env = "ZENODO_SANDBOX_TOKEN" if use_sandbox else "ZENODO_PROD_TOKEN"
        token = self._get_credential(token_env)
        
        return {
            "token": token,
            "use_sandbox": use_sandbox,
            "base_url": "https://sandbox.zenodo.org/api" if use_sandbox 
                       else "https://zenodo.org/api"
        }
    
    def get_github_credentials(self) -> Dict[str, str]:
        """Get GitHub API credentials.
        
        Returns:
            Dictionary with token and repository info
        """
        return {
            "token": self._get_credential("GITHUB_TOKEN"),
            "repository": self._get_credential("GITHUB_REPO"),
            "api_url": "https://api.github.com"
        }
    
    def get_arxiv_credentials(self) -> Dict[str, Optional[str]]:
        """Get arXiv SWORD API credentials (optional).
        
        Returns:
            Dictionary with username and password (may be None)
        """
        return {
            "username": self._get_credential("ARXIV_USERNAME"),
            "password": self._get_credential("ARXIV_PASSWORD"),
            "enabled": bool(self._get_credential("ARXIV_USERNAME"))
        }
    
    def has_zenodo_credentials(self, use_sandbox: bool = True) -> bool:
        """Check if Zenodo credentials are available."""
        creds = self.get_zenodo_credentials(use_sandbox)
        return bool(creds.get("token"))
    
    def has_github_credentials(self) -> bool:
        """Check if GitHub credentials are available."""
        creds = self.get_github_credentials()
        return bool(creds.get("token") and creds.get("repository"))
    
    def has_arxiv_credentials(self) -> bool:
        """Check if arXiv credentials are available."""
        creds = self.get_arxiv_credentials()
        return creds.get("enabled", False)

