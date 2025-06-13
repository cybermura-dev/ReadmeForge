"""Repository for working with the file system."""
import os
import glob
from typing import List, Optional

from ...domain.ports.repositories import FileRepositoryPort


class FileRepository(FileRepositoryPort):
    """Repository for working with the file system."""
    
    def read_file(self, path: str) -> str:
        """
        Reads the content of a file.
        
        Args:
            path: The path to the file
        
        Returns:
            str: The content of the file
            
        Raises:
            FileNotFoundError: If the file is not found
            IOError: If an error occurs while reading the file
        """
        with open(path, 'r', encoding='utf-8') as file:
            return file.read()
    
    def save_file(self, path: str, content: str) -> None:
        """
        Saves the content to a file.
        
        Args:
            path: The path to the file
            content: The content to save
            
        Raises:
            IOError: If an error occurs while writing to a file
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as file:
            file.write(content)
    
    def file_exists(self, path: str) -> bool:
        """
        Checks if a file exists.
        
        Args:
            path: The path to the file
        
        Returns:
            bool: True if the file exists, otherwise False
        """
        return os.path.isfile(path)
    
    def list_files(self, path: str, pattern: Optional[str] = None) -> List[str]:
        """
        Gets a list of files in a directory.
        
        Args:
            path: The path to the directory
            pattern: Optional pattern for filtering files
        
        Returns:
            List[str]: List of file paths
            
        Raises:
            NotADirectoryError: If the path is not a directory
        """
        if not os.path.isdir(path):
            raise NotADirectoryError(f"Path {path} is not a directory")
        
        if pattern:
            search_pattern = os.path.join(path, pattern)
            files = glob.glob(search_pattern)
        else:
            files = [os.path.join(path, f) for f in os.listdir(path) 
                     if os.path.isfile(os.path.join(path, f))]
            
        return files
    
    def join_path(self, *parts: str) -> str:
        """
        Joins parts of a path.
        
        Args:
            *parts: Parts of the path to join
        
        Returns:
            str: Joined path
        """
        return os.path.join(*parts) 