"""Abstract ports for data access."""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, BinaryIO


class FileRepositoryPort(ABC):
    """Abstract port for working with the file system."""
    
    @abstractmethod
    def read_file(self, path: str) -> str:
        """
        Reads the content of a file.
        
        Args:
            path: The path to the file.
        
        Returns:
            str: The content of the file.
        """
        pass
    
    @abstractmethod
    def save_file(self, path: str, content: str) -> None:
        """
        Saves content to a file.
        
        Args:
            path: The path to the file.
            content: The content to save.
        """
        pass
        
    @abstractmethod
    def file_exists(self, path: str) -> bool:
        """
        Checks if a file exists.
        
        Args:
            path: The path to the file.
        
        Returns:
            bool: True if the file exists, otherwise False.
        """
        pass
        
    @abstractmethod
    def list_files(self, path: str, pattern: Optional[str] = None) -> List[str]:
        """
        Gets a list of files in a directory.
        
        Args:
            path: The path to the directory.
            pattern: An optional pattern for filtering files.
        
        Returns:
            List[str]: A list of file paths.
        """
        pass
    
    @abstractmethod
    def join_path(self, *parts: str) -> str:
        """
        Joins path components.
        
        Args:
            *parts: The path components to join.
        
        Returns:
            str: The combined path.
        """
        pass


class ConfigRepositoryPort(ABC):
    """Abstract port for working with configuration."""
    
    @abstractmethod
    def get_config(self, key: Optional[str] = None) -> Any:
        """
        Gets a configuration value by key.
        
        Args:
            key: The configuration key (if None, returns the entire configuration).
        
        Returns:
            Any: The configuration value.
        """
        pass 