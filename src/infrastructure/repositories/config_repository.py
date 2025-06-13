"""Repository for working with configuration."""
import json
import os
from typing import Dict, Any, Optional

from ...domain.ports.repositories import ConfigRepositoryPort, FileRepositoryPort


class ConfigRepository(ConfigRepositoryPort):
    """Repository for working with configuration."""
    
    def __init__(self, config_path: str, file_repository: FileRepositoryPort):
        """
        Initialization of the configuration repository.
        
        Args:
            config_path: The path to the configuration file
            file_repository: Repository for working with files
        """
        self.config_path = config_path
        self.file_repository = file_repository
        self._config_cache = None
    
    def get_config(self, key: Optional[str] = None) -> Any:
        """
        Gets the configuration value by key.
        
        Args:
            key: The key of the configuration (if None, returns the entire configuration)
        
        Returns:
            Any: The configuration value
            
        Raises:
            KeyError: If the key is not found in the configuration
            FileNotFoundError: If the configuration file is not found
            json.JSONDecodeError: If the configuration file has an invalid format
        """
        if self._config_cache is None:
            self._load_config()
        
        if key is None:
            return self._config_cache
        
        if "." in key:
            parts = key.split(".")
            value = self._config_cache
            for part in parts:
                if part in value:
                    value = value[part]
                else:
                    raise KeyError(f"Key '{key}' not found in the configuration")
            return value
        
        if key in self._config_cache:
            return self._config_cache[key]
        
        raise KeyError(f"Key '{key}' not found in the configuration")
    
    def _load_config(self) -> None:
        """
        Loads the configuration from the file.
        
        Raises:
            FileNotFoundError: If the configuration file is not found
            json.JSONDecodeError: If the configuration file has an invalid format
        """
        if not self.file_repository.file_exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        content = self.file_repository.read_file(self.config_path)
        self._config_cache = json.loads(content)
    
    def update_config(self, new_config: Dict[str, Any], merge: bool = True) -> None:
        """
        Updates the configuration.
        
        Args:
            new_config: New configuration values
            merge: If True, merges new values with existing ones,
                   otherwise completely replaces
        """
        if merge and self._config_cache is None:
            try:
                self._load_config()
            except (FileNotFoundError, json.JSONDecodeError):
                self._config_cache = {}
        
        if merge and self._config_cache is not None:
            self._deep_update(self._config_cache, new_config)
        else:
            self._config_cache = new_config
        
        self._save_config()
    
    def _deep_update(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        Recursively updates the target dictionary with values from the source.
        
        Args:
            target: Target dictionary
            source: Dictionary with new values
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value
    
    def _save_config(self) -> None:
        """
        Saves the current configuration to a file.
        
        Raises:
            IOError: If an error occurs while writing to a file
        """
        content = json.dumps(self._config_cache, indent=2)
        self.file_repository.save_file(self.config_path, content)